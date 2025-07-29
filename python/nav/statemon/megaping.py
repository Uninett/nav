#
# Copyright (C) 2011, 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Ping multiple hosts at once."""

import threading
import time
import socket
import select
import os
import random
import logging
import hashlib

from nav.daemon import safesleep as sleep
from nav.statemon import config

from .icmppacket import ICMP_MINLEN, PacketV4, PacketV6


_logger = logging.getLogger(__name__)


def make_sockets():
    """Makes and returns the raw IPv6 and IPv4 ICMP sockets.

    This needs to run as root before dropping privileges.

    """
    try:
        socketv6 = socket.socket(
            socket.AF_INET6, socket.SOCK_RAW, socket.getprotobyname('ipv6-icmp')
        )
    except Exception:  # noqa: BLE001
        _logger.error("Could not create v6 socket")
        raise

    try:
        socketv4 = socket.socket(
            socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname('icmp')
        )
    except Exception:  # noqa: BLE001
        _logger.error("Could not create v4 socket")
        raise

    return [socketv6, socketv4]


class Host(object):
    """
    Contains the destination address and current sequence number of a host.
    """

    COOKIE_LENGTH = len(hashlib.new('md5').digest())

    def __init__(self, ip):
        self.ip = ip
        # Random value for the cookie
        self.rnd = random.randint(10000, 2**16 - 1)
        # Time the echo was sent
        self.time = 0
        # Used in nextseq
        self.certain = 0

        # Check IP version and choose packet class
        if self.is_valid_ipv6():
            self.ipv6 = True
            self.packet = PacketV6()
        else:
            self.ipv6 = False
            self.packet = PacketV4()

        self.packet.id = os.getpid() % 65536
        self.reply = None

    def make_packet(self, size, cookie=None):
        """Makes the next echo reply packet"""
        if not cookie:
            cookie = self.make_cookie()
        self.packet.data = cookie.ljust(size - ICMP_MINLEN)
        return self.packet.assemble(), cookie

    def make_cookie(self):
        """Makes and returns a request identifier to be used as data in a ping
        packet.
        """
        cookie = hashlib.new('md5')
        cookie.update(self.ip.encode('ASCII'))
        cookie.update(str(self.rnd).encode('ASCII'))
        cookie.update(str(self.time).encode('ASCII'))
        return cookie.digest()

    def is_v6(self):
        """
        Returns True if host is v6
        """
        return self.ipv6

    def is_valid_ipv6(self):
        """Help method to check if addr is IPv6"""
        try:
            socket.inet_pton(socket.AF_INET6, self.ip)
            return True
        except socket.error:
            return False

    def is_valid_ipv4(self):
        """Help method to check if addr is v4"""
        try:
            socket.inet_pton(socket.AF_INET, self.ip)
            return True
        except socket.error:
            return False

    def next_seq(self):
        """Increments the echo request sequence number to use with the next
        request.

        Wrap around at 65536 (values must be unsigned short).

        """
        self.packet.sequence = (self.packet.sequence + 1) % 2**16
        if not self.certain and self.packet.sequence > 2:
            self.certain = 1

    def __repr__(self):
        return "Host instance for IP %s with sequence number %s " % (
            self.ip,
            self.packet.sequence,
        )


class MegaPing(object):
    """
    Sends icmp echo to multiple hosts in parallell.
    Typical use:
    pinger = megaping.MegaPing()
    pinger.set_hosts(['127.0.0.1','10.0.0.1'])
    timeUsed = pinger.ping()
    results = pinger.results()
    """

    _requests = _sender = _getter = _sender_finished = None

    def __init__(self, sockets, conf=None):
        # Get config in /etc/pping.conf
        if conf is None:
            try:
                self._conf = config.pingconf()
            except Exception:  # noqa: BLE001
                _logger.critical("Failed to open config file. Using default values.")
                self._conf = {}
        else:
            self._conf = conf

        # Delay between each packet is transmitted
        self._delay = float(self._conf.get('delay', 2)) / 1000  # convert from ms
        # Timeout before considering hosts as down
        self._timeout = int(self._conf.get('timeout', 5))
        # Dictionary with all the hosts, populated by set_hosts()
        self._hosts = {}

        packetsize = int(self._conf.get('packetsize', 64))
        if packetsize < 44:
            raise ValueError(
                (
                    "Packetsize (%s) too small to create a proper "
                    "cookie; Must be at least 44."
                )
                % packetsize
            )
        self._packetsize = packetsize
        self._pid = os.getpid() % 65536

        # Global timing of the ppinger
        self._elapsedtime = 0

        # Initialize the sockets
        if sockets is not None:
            self._sock6 = sockets[0]
            self._sock4 = sockets[1]
        else:
            try:
                sockets = make_sockets()
            except Exception:  # noqa: BLE001
                _logger.error("Tried to create sockets without being root!")

            self._sock6 = sockets[0]
            self._sock4 = sockets[1]
            _logger.info("No sockets passed as argument, creating own")

    def set_hosts(self, ips):
        """
        Specify a list of ip addresses to ping. If we alredy have the host
        in our list, we reuse that host object to ensure proper sequence
        increment
        """
        # add new hosts
        currenthosts = {}
        for ip in ips:
            if ip not in self._hosts:
                currenthosts[ip] = Host(ip)
            else:
                currenthosts[ip] = self._hosts[ip]
        self._hosts = currenthosts

    def reset(self):
        """
        Reset method to clear requests and responses
        """
        self._requests = {}
        for host in self._hosts.values():
            host.reply = None
        self._sender_finished = 0

    def ping(self):
        """
        Send icmp echo to all configured hosts. Returns the
        time used.
        """
        # Start working
        self.reset()
        self._sender = threading.Thread(target=self._send_requests, name="sender")
        self._getter = threading.Thread(target=self._get_responses, name="getter")
        self._sender.daemon = True
        self._getter.daemon = True
        self._sender.start()
        self._getter.start()
        self._getter.join()
        return self._elapsedtime

    def _send_requests(self):
        # Get ip addresses to ping
        hosts = self._hosts.values()

        # Ping each host
        for host in hosts:
            host.time = time.time()
            # create and save a request identifier
            packet, cookie = host.make_packet(self._packetsize)
            self._requests[cookie] = host
            host.next_seq()

            try:
                if not host.is_v6():
                    self._sock4.sendto(packet, (host.ip, 0))
                else:
                    self._sock6.sendto(packet, (host.ip, 0, 0, 0))
            except Exception as error:  # noqa: BLE001
                _logger.info("Failed to ping %s [%s]", host.ip, error)

            sleep(self._delay)
        self._sender_finished = time.time()

    def _get_responses(self):
        start = time.time()
        timeout = self._timeout

        while not self._sender_finished or self._requests:
            if self._sender_finished:
                runtime = time.time() - self._sender_finished
                if runtime > self._timeout:
                    break
                else:
                    timeout = self._timeout - runtime

            # Listen for incoming data on sockets
            readable, _wt, _er = select.select(
                [self._sock6, self._sock4], [], [], timeout
            )

            # If data found
            if readable:
                # okay to use time here, because select has told us
                # there is data and we don't care to measure the time
                # it takes the system to give us the packet.
                arrival = time.time()

                # Find out which socket got data and read
                for sock in readable:
                    try:
                        raw_pong, sender = sock.recvfrom(4096)
                    except socket.error:
                        _logger.critical("RealityError -2", exc_info=True)
                        continue

                    is_ipv6 = sock == self._sock6
                    self._process_response(raw_pong, sender, is_ipv6, arrival)
            elif self._sender_finished:
                break

        # Everything else timed out
        for host in self._requests.values():
            host.reply = None
        end = time.time()
        self._elapsedtime = end - start

    def _process_response(self, raw_pong, sender, is_ipv6, arrival):
        # Extract header info and payload
        packet_class = PacketV6 if is_ipv6 else PacketV4
        try:
            pong = packet_class(raw_pong)
        except Exception as error:  # noqa: BLE001
            _logger.critical("could not disassemble packet from %r: %s", sender, error)
            return

        if pong.type != pong.ICMP_ECHO_REPLY:
            # we only care about echo replies
            _logger.debug("Packet from %s was not an echo reply, but %s", sender, pong)
            return

        if not pong.id == self._pid:
            _logger.debug(
                "packet from %r doesn't match our id (%s): %r (raw packet: %r)",
                sender,
                self._pid,
                pong,
                raw_pong,
            )
            return

        cookie = pong.data[: Host.COOKIE_LENGTH]

        # Find the host with this cookie
        try:
            host = self._requests[cookie]
        except KeyError:
            _logger.debug(
                "packet from %r does not match any outstanding "
                "request: %r (raw packet: %r cookie: %r)",
                sender,
                pong,
                raw_pong,
                cookie,
            )
            return

        # Delete the entry of the host who has replied and add the pingtime
        pingtime = arrival - host.time
        host.reply = pingtime
        _logger.debug("Response from %-16s in %03.3f ms", sender, pingtime * 1000)
        del self._requests[cookie]

    def results(self):
        """
        Returns a tuple of
        (ip, roundtriptime) for all hosts.
        Unreachable hosts will have roundtriptime = -1
        """
        return [
            (host.ip, host.reply if host.reply else -1) for host in self._hosts.values()
        ]

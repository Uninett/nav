#
# Copyright (C) 2002-2004 Norwegian University of Science and Technology
# Copyright (C) 2011, 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
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
import sys
import time
import socket
import select
import os
import random
import struct
import circbuf
import config
import hashlib
from debug import debug

from nav.daemon import safesleep as sleep

from .icmppacket import ICMP_MINLEN, PacketV4, PacketV6

# Global method to create the sockets as root before the process changes user
def makeSockets():
    try:
        socketv6 = socket.socket(socket.AF_INET6, socket.SOCK_RAW,
                                 socket.getprotobyname('ipv6-icmp'))
    except:
        debug("Could not create v6 socket")

    try:
        socketv4 = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                 socket.getprotobyname('icmp'))
    except:
        debug("Could not create v6 socket")

    return [socketv6, socketv4]

class Host(object):
    COOKIE_LENGTH = len(hashlib.md5().digest())

    def __init__(self, ip):
        self.rnd = random.randint(10000, 2**16-1)
        self.time = 0
        self.certain = 0
        self.ip = ip

        if self.is_valid_ipv6(ip):
            self.ipv6 = True
            self.packet = PacketV6()
        else:
            self.ipv6 = False
            self.packet = PacketV4()
        self.packet.id = os.getpid() % 65536
        self.replies = circbuf.CircBuf()

    def make_packet(self, size, cookie=None):
        """Makes the next echo reply packet"""
        if not cookie:
            cookie = self.make_cookie()
        self.packet.data = cookie.ljust(size-ICMP_MINLEN)
        return (self.packet.assemble(), cookie)

    def make_cookie(self):
        """Makes and returns a request identifier to be used as data in a ping
        packet.

        """
        hash = hashlib.md5()
        hash.update(self.ip)
        hash.update(str(self.rnd))
        hash.update(str(self.time))
        return hash.digest()

    def is_v6(self):
        return self.ipv6
    
    # Help method
    def is_valid_ipv6(self, addr):
        try:
            socket.inet_pton(socket.AF_INET6, addr)
            return True
        except socket.error:
            return False

    # Help method
    def is_valid_ipv4(self, addr):
        try:
            socket.inet_pton(socket.AF_INET, addr)
            return True
        except socket.error:
            return False

    def getseq(self):
        return self.packet.id

    def nextseq(self):
        """Increments the echo request sequence number to use with the next
        request.

        Wrap around at 65536 (values must be unsigned short).

        """
        self.packet.sequence = (self.packet.sequence + 1) % 2**16
        if not self.certain and self.packet.sequence > 2:
            self.certain = 1

    def __hash__(self):
        return self.ip.__hash__()

    def __eq__(self, obj):
        if type(obj) == type(''):
            return self.ip == obj
        else:
            return self.ip == obj.ip
    def __repr__(self):
        return "megaping.Host instance for ip %s " % self.ip

    def getState(self, nrping=3):
        # This is the reoundtrip time. Not sure if we need
        # status bit as well...
        return self.replies[0]

class MegaPing:
    """
    Sends icmp echo to multiple hosts in parallell.
    Typical use:
    pinger = megaping.MegaPing()
    pinger.setHosts(['127.0.0.1','10.0.0.1'])
    timeUsed = pinger.ping()
    hostsUp = pinger.answers()
    hostsDown = pinger.noAnswers()
    """
    def __init__(self, sockets, conf=None):
        if conf is None:
            try:
                self._conf = config.pingconf()
            except:
                debug("Failed to open config file. Using default values.", 2)
                self._conf = {}
        else:
            self._conf = conf
        # delay between each packet is transmitted
        self._delay = float(self._conf.get('delay', 2))/1000  # convert from ms
        # Timeout before considering hosts as down
        self._timeout = int(self._conf.get('timeout', 5))
        self._hosts = {}
        packetsize = int(self._conf.get('packetsize', 64))
        if packetsize < 44:
            raise """Packetsize (%s) too small to create a proper cookie.
                             Must be at least 44.""" % packetsize
        self._packetsize = packetsize
        self._pid = os.getpid() % 65536
        self._elapsedtime = 0

        # Initialize the sockets
        if not sockets == None:
            self._sock6 = sockets[0]
            self._sock4 = sockets[1]
        else:
            try:
                sockets = makeSockets()
            except:
                debug("Tried to create sockets without beeing root!")

            self._sock6 = sockets[0]
            self._sock4 = sockets[1]
            debug("No sockets passed as argument, creating own")

    def setHosts(self, ips):
        """
        Specify a list of ip addresses to ping. If we alredy have the host
        in our list, we reuse that host object to ensure proper sequence
        increment
        """
        # add new hosts
        currenthosts = {}
        for ip in ips:
            if not self._hosts.has_key(ip):
                currenthosts[ip] = Host(ip)
                currenthosts[ip] = Host(ip)
            else:
                    currenthosts[ip] = self._hosts[ip]
        self._hosts = currenthosts

    def reset(self):
        self._requests = {}
        self.responses = {}
        self._senderFinished = 0

    def ping(self):
        """
        Send icmp echo to all configured hosts. Returns the
        time used.
        """
        # Start working
        self.reset()
        #kwargs = {'mySocket': makeSocket()}
        self._sender = threading.Thread(target=self._sendRequests, name="sender")
        self._getter = threading.Thread(target=self._getResponses, name="getter")
        self._sender.setDaemon(1)
        self._getter.setDaemon(1)
        self._sender.start()
        self._getter.start()
        self._getter.join()
        return self._elapsedtime


    def _getResponses(self):
        start = time.time()
        timeout = self._timeout

        while not self._senderFinished or self._requests:
            if self._senderFinished:
                runtime = time.time() - self._senderFinished
                if runtime > self._timeout:
                    break
                else:
                    timeout = self._timeout - runtime

            startwait = time.time()

            # Listen for incoming data on sockets
            rd, wt, er = select.select([self._sock6, self._sock4], [], [],
                                       timeout)

            # If data found
            if rd:
                # okay to use time here, because select has told us
                # there is data and we don't care to measure the time
                # it takes the system to give us the packet.
                arrival = time.time()

                # Find out which socket got data and read
                for sock in rd:
                    try:
                        raw_pong, sender = sock.recvfrom(4096)
                    except socket.error, e:
                        debug("RealityError -2: %s" % e, 1)
                        continue

                    is_ipv6 = sock == self._sock6
                    self._processResponse(raw_pong, sender, is_ipv6, arrival)
            elif self._senderFinished:
                break

        # Everything else timed out
        for host in self._requests.values():
            host.replies.push(None)
        end = time.time()
        self._elapsedtime = end - start


    def _processResponse(self, raw_pong, sender, is_ipv6, arrival):
        # Extract header info and payload
        packet_class = PacketV6 if is_ipv6 else PacketV4
        try:
            pong = packet_class(raw_pong)
        except Exception, error:
            debug("could not disassemble packet from %r: %s" % (
                    sender, error), 2)
            return

        if pong.type != pong.ICMP_ECHO_REPLY:
            # we only care about echo replies
            return

        if not pong.id == self._pid:
            debug("packet from %r doesn't match our id "
                  "(%s): %r (raw packet: %r)" % (sender, self._pid, pong,
                                                 raw_pong), 7)
            return

        cookie = pong.data[:Host.COOKIE_LENGTH]

        # Find the host with this cookie
        try:
            host = self._requests[cookie]
        except KeyError:
            debug("packet from %r does not match any outstanding request: "
                  "%r (raw packet: %r cookie: %r)" % (sender, pong, raw_pong,
                                                      cookie), 7)
            return

        # Delete the entry of the host who has replied and add the pingtime
        pingtime = arrival - host.time
        host.replies.push(pingtime)
        debug("Response from %-16s in %03.3f ms" %
              (sender, pingtime*1000), 7)
        del self._requests[cookie]


    def _sendRequests(self, mySocket=None, hosts=None):

        # Get ip addresses to ping
        hosts = self._hosts.values()

        # Ping each host
        for host in hosts:
            if self._requests.has_key(host):
                debug("Duplicate host %s ignored" % host, 6)
                continue

            host.time = time.time()
            # create and save a request identifier
            packet, cookie = host.make_packet(self._packetsize)
            self._requests[cookie] = host
            host.nextseq()

            try:
                if not host.is_v6():
                    self._sock4.sendto(packet, (host.ip, 0))
                else:
                    self._sock6.sendto(packet, (host.ip, 0, 0, 0))
            except Exception, error:
                debug("Failed to ping %s [%s]" % (host.ip, error), 5)

            sleep(self._delay)
        self._senderFinished = time.time()

    def results(self):
        """
        Returns a tuple of
        (ip, roundtriptime) for all hosts.
        Unreachable hosts will have roundtriptime = -1
        """
        reply = []
        for host in self._hosts.values():
            if host.getState():
                reply.append((host.ip, host.replies[0]))
            else:
                reply.append((host.ip, -1))
        return reply

    def noAnswers(self):
        """
        Returns a tuple of
        (ip, timeout) for the unreachable hosts.
        """
        reply = []
        for host in self._hosts.values():
            if not host.getState():
                reply.append((host.ip, self._timeout))
        return reply

    def answers(self):
        """
        Returns a tuple of
        (ip, roundtriptime) for reachable hosts.
        """
        reply = []
        for host in self._hosts.values():
            if host.getState():
                reply.append((host.ip, host.replies[0]))
        return reply

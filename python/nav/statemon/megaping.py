# -*- coding: ISO8859-1 -*-
#
# Copyright 2002-2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Stian Soiland   <stain@itea.ntnu.no>

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
from debug import debug

from nav.daemon import safesleep as sleep

# From our friend:
import ip
import icmp

# updating rrd should be moved out
# import rrd

PINGSTRING = "Stian og Magnus ruler verden"

def makeSocket():
    sock = socket.socket(socket.AF_INET,
                       socket.SOCK_RAW,
                       socket.IPPROTO_ICMP)
    sock.setblocking(1)
    return sock

class Host:
    def __init__(self, ip):
        self.rnd = random.randint(0, 2**16-1)
        self.certain = 0
        self.ip = ip
        self.pkt = icmp.Packet()
        self.pkt.type = icmp.ICMP_ECHO
        self.pkt.id = os.getpid() % 65536
        self.pkt.seq = 0
        self.replies = circbuf.CircBuf()

    def makePacket(self, pingstring=PINGSTRING):
        self.pkt.data = pingstring
        return self.pkt.assemble()

    def getseq(self):
        return self.pkt.seq

    def nextseq(self):
        self.pkt.seq = (self.pkt.seq + 1) % 2**16
        if not self.certain and self.pkt.seq > 2:
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
    def __init__(self, socket=None, conf=None):
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

        # Create our common socket
        if socket is None:
            self._sock = makeSocket()
        else:
            self._sock = socket

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
            rd, wt, er = select.select([self._sock], [], [], timeout)
            if rd:
                # okay to use time here, because select has told us
                # there is data and we don't care to measure the time
                # it takes the system to give us the packet.
                arrival = time.time()
                try:
                    (pkt, (sender, blapp)) = self._sock.recvfrom(4096)
                except socket.error:
                    debug("RealityError -2", 1)
                    continue
                # could also use the ip module to get the payload

                repip = ip.Packet(pkt)
                try:
                    reply = icmp.Packet(repip.data)
                except ValueError:
                    debug("Recived illegeal packet from %s: %s" % (sender,
                          repr(repip.data)), 7)
                    continue
                if reply.id <> self._pid:
                    debug("The id field of the packet does not match for %s" %
                          sender, 7)
                    continue

                cookie = reply.data[0:14]
                try:
                    host = self._requests[cookie]
                except KeyError:
                    debug("The packet recieved from %s does not match any of "
                          "the packets we sent." % repr(sender), 7)
                    debug("Length of recieved packet: %i Cookie: [%s]" %
                          (len(reply.data), cookie), 7)
                    continue

                # Puuh.. OK, it IS our package <--- Stain, you're a moron
                pingtime = arrival - host.time
                ### Insert answer to circbuf
                host.replies.push(pingtime)

                #host.logPingTime(pingtime)

                debug("Response from %-16s in %03.3f ms" %
                      (sender, pingtime*1000), 7)
                del self._requests[cookie]
            elif self._senderFinished:
                    break

        # Everything else timed out
        for host in self._requests.values():
            host.replies.push(None)
            #host.logPingTime(None)
        end = time.time()
        self._elapsedtime = end - start


    def _sendRequests(self, mySocket=None, hosts=None):
        if mySocket is None:
            mySocket = self._sock
        if hosts is None:
            hosts = self._hosts.values()
        for host in hosts:
            if self._requests.has_key(host):
                debug("Duplicate host %s ignored" % host, 6)
                continue

            now = time.time()
            host.time = now
            #convert ip to chr (hex notation)
            chrip = "".join(map(lambda x:chr(int(x)), host.ip.split('.')))
            packedtime = struct.pack('d', now)
            packedrnd = struct.pack('H', host.rnd)
            identifier = ''.join([chrip, packedtime, packedrnd])
            cookie = identifier.ljust(self._packetsize-icmp.ICMP_MINLEN)
            # typical cookie: "\x81\xf18F\x06\xf13\xc9\x87\xa8\xceA\xe5m"
            # the cookie is 14 bytes long
            self._requests[identifier] = host
            packet = host.makePacket(cookie)
            host.nextseq()
            try:
                mySocket.sendto(packet, (host.ip, 0))
            except Exception, e:
                debug("Failed to ping %s [%s]" % (host.ip, str(e)), 5)
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

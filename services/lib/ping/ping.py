#!/usr/bin/env python

# Copyright 1997, Corporation for National Research Initiatives
# written by Jeremy Hylton, jeremy@cnri.reston.va.us

"""Ping. Round-trip delay measurement utility.

Uses ICMP ECHO_REQEST messages to measure the delay between two
Internet hosts.
"""

import icmp, ip
import socket
import time
import select
import string
import os, sys

TimedOut = 'TimedOut'

class PingSocket:

    def __init__(self, addr):
	self.dest = (socket.gethostbyname(addr), 0)
	self.open_icmp_socket()

    def open_icmp_socket(self):
	self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW,
				    socket.IPPROTO_ICMP)
	self.socket.setblocking(1)

    def sendto(self, packet):
	self.socket.sendto(packet, self.dest)

    def recvfrom(self, maxbytes):
	return self.socket.recvfrom(maxbytes)

class Pinger:

    def __init__(self, addr, num):
	self.num = num
	self.last = 0
	self.sent = 0
	self.times = {}
	self.deltas = []
	self.sock = PingSocket(addr)
	self.pid = os.getpid()
	self.addr = addr
	name, aliases, ipaddr = socket.gethostbyaddr(addr)
	if aliases:
	    self.destinfo = (aliases[0], ipaddr[0])
	else:
	    self.destinfo = (name, ipaddr[0])

    def send_packet(self):
	pkt = icmp.Packet()
	pkt.type = icmp.ICMP_ECHO
	pkt.id = self.pid
	pkt.seq = self.sent
	pkt.data = 'python pinger'
	buf = pkt.assemble()
	self.times[self.sent] = time.time()
	self.sock.sendto(buf)
	self.plen = len(buf)
	self.sent = self.sent + 1

    def recv_packet(self, pkt, when):
	try:
	    sent = self.times[pkt.seq]
	    del self.times[pkt.seq]
	except KeyError:
	    return
	# limit to ms precision
	delta = int((when - sent) * 1000.)
	self.deltas.append(delta)
	self.recv_output(self.plen, self.destinfo[0],
			 self.destinfo[1], pkt.seq, delta)
	if pkt.seq > self.last:
	    self.last = pkt.seq

    def recv_output(self, bytes, dest, addr, seq, delta):
	"Place holder for subclass output/collector method"
	pass

    def ping(self):
	# don't wait more than 10 seconds from now for first reply
	self.last_arrival = time.time()
	while 1:
	    if self.sent < self.num:
		self.send_packet()
	    elif not self.times and self.last == self.num - 1:
		break
	    else:
		now = time.time()
		if self.deltas:
		    # Wait no more than 10 times the longest delay so far
		    if (now - self.last_arrival) > max(self.deltas) / 100.:
			break
		else:
		    # Wait no more than 10 seconds
		    if (now - self.last_arrival) > 10.:
			break
	    self.wait()

    def wait(self):
	start = time.time()
	timeout = 1.0
	while 1:
	    rd, wt, er = select.select([self.sock.socket], [], [], timeout)
	    if rd:
		# okay to use time here, because select has told us
		# there is data and we don't care to measure the time
		# it takes the system to give us the packet.
		arrival = time.time()
		try:
		    pkt, who = self.sock.recvfrom(4096)
		except socket.error:
		    continue
		# could also use the ip module to get the payload
		repip = ip.Packet(pkt)
		try:
		    reply = icmp.Packet(repip.data)
		except ValueError:
		    continue
		if reply.id == self.pid:
		    self.recv_packet(reply, arrival)
		    self.last_arrival = arrival
	    timeout = (start + 1.0) - time.time()
	    if timeout < 0:
		break
	    
    def get_summary(self):
	dmin = min(self.deltas)
	dmax = max(self.deltas)
	davg = reduce(lambda x, y: x + y, self.deltas) / len(self.deltas)
	sent = self.num
	recv = sent - len(self.times.values())
	loss = float(sent - recv) / float(sent)
	return dmin, davg, dmax, sent, recv, loss

class CollectorPinger(Pinger):

    def __init__(self, host, num):
	Pinger.__init__(self, host, num)
	self.results = {}

    def recv_output(self, bytes, dest, addr, seq, delta):
	self.results[seq] = delta

class CmdlinePinger(Pinger):

    def recv_output(self, bytes, dest, addr, seq, delta):
	print "%d bytes from %s (%s): icmp_seq=%d. time=%d. ms" % \
	      (bytes, dest, addr, seq, delta)

    def ping(self):
	print "PING %s" % self.destinfo[0]
	Pinger.ping(self)	

if __name__ == "__main__":    
    try:
	who = sys.argv[1]
    except IndexError:
	print "ping.py host [#packets]"
	sys.exit(0)
    try:
	num = string.atoi(sys.argv[2])
    except ValueError:
	print "ping.py host [#packets]"
	sys.exit(0)
    except IndexError:
	num = 32

    p = CmdlinePinger(who, num)
    p.ping()
    summary = p.get_summary()
    print "---Ping statistics---"
    print "%d packets transmitted, %d packets received, %d%% packet loss" % \
	  (summary[3], summary[4], int(summary[5] * 100.))
    print "round-trip (ms)   min/avg/max = %d/%d/%d" % \
	  (summary[0], summary[1], summary[2])


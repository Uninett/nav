#!/usr/bin/env python

# Copyright 1997, Corporation for National Research Initiatives
# written by Jeremy Hylton, jeremy@cnri.reston.va.us

import ip, icmp, udp
import socket
import select
import time
import os
import getopt
import string

class Tracer:

    def __init__(self, host):
	self.id = (os.getpid() & 0xffff) | 0x8000
	self.init_probe_packet(os.uname()[1], host)
	self.times = {}
	self.got_there = None
	# control be
	self.def_port = 32768 + 666
	self.max_ttl = 30
	self.max_wait = 3.0
	self.nqueries = 3

    def open_sockets(self):
	# might want to do setuid(getuid) when we're done with this
	self.icmp_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
				       socket.IPPROTO_ICMP)
	self.ip_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
				     socket.IPPROTO_RAW)
	self.ip_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,
				self.packlen) 
	self.ip_sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1) 

    def init_probe_packet(self, src, dest):
	# build the packet, then set its length 
	p = ip.Packet()
	p.dst = dest
	p.p = socket.IPPROTO_UDP

	u = udp.Packet()
	u.sport = self.id
	u.data = 'python traceroute' * 4
	# need to set up the lengths
	p.data = u.assemble()
	self.probe_ip = p
	self.probe_udp = u
	self.packlen = len(p.assemble())

    def send_probe(self, seq, ttl):
	self.probe_ip.ttl = ttl
	self.probe_ip.id = self.id + seq
	self.probe_udp.dport = self.def_port + seq
	self.probe_ip.data = self.probe_udp.assemble(0)
	now = time.time()
	self.ip_sock.sendto(self.probe_ip.assemble(0),
			    (self.probe_ip.dst, 0))
	return now

    def get_reply(self, seq):
	start = time.time()
	timeout = self.max_wait
	while 1:
	    rd, wt, er = select.select([self.icmp_sock], [], [],
				       timeout)
	    if rd:
		try:
		    pkt, who = self.icmp_sock.recvfrom(4096)
		except socket.error:
		    pass
		arrived = time.time()
		_reply = ip.Packet(pkt)
		reply = icmp.Packet(_reply.data)
		if (reply.type == icmp.ICMP_TIMXCEED \
		    and reply.code == icmp.ICMP_TIMXCEED_INTRANS) \
		    or reply.type == icmp.ICMP_UNREACH:
		    encap = ip.Packet(reply.data)	
		    # what about this checksum?
		    orig = udp.Packet(encap.data, 0)
		    if orig.sport == self.id \
		       and orig.dport == self.def_port+seq:
			if reply.type == icmp.ICMP_UNREACH:
			    self.got_there = 1
			return _reply, arrived
	    timeout = (start + self.max_wait) - time.time()
	    if timeout < 0:
		return None, None
		

    def trace(self):
	seq = 0
	self.got_there = 0
	for ttl in range(1, self.max_ttl+1):
	    deltas = []
	    hosts = {}
	    for i in range(self.nqueries):
		seq = seq + 1
		send_at = self.send_probe(seq, ttl)
		reply, recv_at = self.get_reply(seq)
		if reply:
		    delta = recv_at - send_at
		    deltas.append(delta * 1000.)
		    hosts[reply.src] = 1
		    # gives option to look for multiple routers replying
		else:
		    deltas.append(-1.)
	    # but I'm going to bail on doing anything about multiple
	    # hosts responding  
	    if hosts:
		pick_a_host = hosts.keys()[0]
	    else:
		pick_a_host = ''
	    self.trace_summary(ttl, hosts.keys()[0], deltas)
	    if self.got_there:
		break

    def trace_summary(self, ttl, host, deltas):
	pass

class CollectorTracer(Tracer):
    
    def __init__(self, host):
	Tracer.__init__(self, host)
	self.results = {}

    def trace_summary(self, ttl, host, deltas):
	self.results[ttl] = (host, deltas)
	
class CmdlineTracer(Tracer):
    
    def __init__(self, host):
	Tracer.__init__(self, host)
	self.resolve_host = 1
	self.output_style = 2

    def trace_summary(self, ttl, host, deltas):
	if resolve_host:
	    try:
		name, aliases, ipaddr = socket.gethostbyaddr(host)
		if aliases:
		    name = aliases[0]
	    except socket.error:
		name = host
	    print " %d  %s (%s) " % (ttl, name, host),
	else:
	    print " %d  %s" % (ttl, host),
	if output_style == 2:
	    print "\n\t",
	for delta in deltas:
	    if delta > 0.:
		print " %7.3f ms  " % (delta),
	    else:
		print "    *        ",
	print
    


def usage():
    usage = \
"""Usage: traceroute.py [-m max_ttl] [-n] [-p port] [-q nqueries] [-w wait] [-s]
                 host
"""
    print usage

def parse_options(args, tracer):
    opts, args = getopt.getopt(args, 'snm:p:q:w:')
    for k, v in opts:
	if k == '-n':
	    tracer.resolve_host = 0
	elif k == '-s':
	    tracer.output_style = 1
	elif k == '-m':
	    try:
		hops = string.atoi(v)
		tracer.max_ttl = hops
	    except ValueError:
		print "invalid max_ttl value", v
		return []
	elif k == '-p':
	    global def_port
	    try:
		port = string.atoi(v)
		tracer.def_port = port
	    except ValueError:
		print "invalid port", v
		return []
	elif k == '-q':
	    try:
		n = string.atoi(v)
		tracer.nqueries = n
	    except ValueError:
		print "invalid number of queries", v
		return []
	elif k == '-w':
	    try:
		w = string.atoi(v)
		tracer.max_wait = float(w)
	    except ValueError:
		print "invalid timeout", w
		return []
    return args
    
def main():
    import sys
    t = CmdlineTracer(host[0])
    host = parse_options(sys.argv[1:], t)
    if len(host) != 1:
	usage()
	return
    t.open_sockets()
    t.trace()

if __name__ == "__main__":
    main()

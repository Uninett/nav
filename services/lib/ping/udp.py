"""UDP packets."""

# Copyright 1997, Corporation for National Research Initiatives
# written by Jeremy Hylton, jeremy@cnri.reston.va.us

import inet
import struct
import string

class Packet:

    def __init__(self, packet=None, cksum=1):
	if packet:
	    self.__disassemble(packet, cksum)
	else:
	    self.sport = 0
	    self.dport = 0
	    self.ulen = 8
	    self.sum = 0
	    self.data = ''

    def __repr__(self):
	begin = "<UDP %d->%d len=%d " % (self.sport, self.dport, self.ulen)
	if self.ulen == 8:
	    rep = begin + "\'\'>"
	elif self.ulen < 18:
	    rep = begin + "%s>" % repr(self.data)
	else:
	    rep = begin + "%s>" % repr(self.data[:10] + '...')
	return rep
	    

    def assemble(self, cksum=1):
	self.ulen = 8 + len(self.data)
	begin = struct.pack('hhh', self.sport, self.dport, self.ulen)
	packet = begin + '\000\000' + self.data
	if cksum:
	    self.sum = inet.cksum(packet)
	    packet = begin + struct.pack('h', self.sum) + self.data
	self.__packet = inet.udph2net(packet)
	return self.__packet

    def __disassemble(self, raw_packet, cksum=1):
	packet = inet.net2updh(raw_packet)
	if cksum and packet[6:8] != '\000\000':
	    our_cksum = inet.cksum(packet)
	    if our_cksum != 0:
		raise ValueError, packet
	elts = map(lambda x:x & 0xffff, struct.unpack('hhhh', packet[:8]))
	[self.sport, self.dport, self.ulen, self.sum] = elts
	self.data = packet[8:]

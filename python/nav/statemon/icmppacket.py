#
# Copyright (C) 23. Feb. 2004 - Lars Strand <lars strand at gnist org>
# Copyright (C) 2011 UNINETT AS
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
import struct
import array
import socket
import time


ICMP_DATA_STR = 56
ICMP_TYPE = 8
ICMP_TYPE_IP6 = 128
ICMP_CODE = 0
ICMP_CHECKSUM = 0
ICMP_ID = 0
ICMP_SEQ_NR = 0


class PacketV4(object):

    def __init__(self, id=None, load=None):
        self.id = id
        self.load = load
        self.size = ICMP_DATA_STR
        self.packet = None
        self.header = None


    def construct(self):
        """Constructs a ICMP echo packet of variable size"""
        # size must be big enough to contain time sent
        if self.size < int(struct.calcsize("d")):
            _error("packetsize to small, must be at least %d" % int(struct.calcsize("d")))

        header = self._construct_header()

        # space for time
        self.size -= struct.calcsize("d")

        # construct payload based on size, may be omitted :)
        rest = ""
        if self.size > len(self.load):
            rest = self.load
            self.size -= len(self.load)

        # pad the rest of payload
        rest += self.size * "X"

        # pack
        data = struct.pack("d", time.time()) + rest
        packet = header + data          # ping packet without checksum
        checksum = self._in_cksum(packet)    # make checksum

        header = self._construct_header(checksum)

        self.header = header
        self.data   = data    
        self.checksum = checksum
        # ping packet *with* checksum
        packet = header + data

        # a perfectly formatted ICMP echo packet
        self.packet = packet

    def _construct_header(self, checksum=ICMP_CHECKSUM):
        return struct.pack('bbHHh', ICMP_TYPE, ICMP_CODE, checksum,
                           ICMP_ID, ICMP_SEQ_NR+self.id)


    def _in_cksum(self,packet):
        """THE RFC792 states: 'The 16 bit one's complement of
        the one's complement sum of all 16 bit words in the header.'

        Generates a checksum of a (ICMP) packet. Based on in_chksum found
        in ping.c on FreeBSD.
        """

        # add byte if not dividable by 2
        if len(packet) & 1:
            packet = packet + '\0'

        # split into 16-bit word and insert into a binary array
        words = array.array('h', packet)
        sum = 0

        # perform ones complement arithmetic on 16-bit words
        for word in words:
            sum += (word & 0xffff)

        hi = sum >> 16
        lo = sum & 0xffff
        sum = hi + lo
        sum = sum + (sum >> 16)

        return (~sum) & 0xffff # return ones complement

    def unpack(self, packet):
        self.packet = packet
        self.header = self.packet[20:28]
        _type, code, chksum, _id, seqnr = struct.unpack("bbHHh", self.header)
        self.id = seqnr
        self.load = self.packet[36:73]

    def get_id(self):
        return self.id

    def get_load(self):
        return self.load

class PacketV6(PacketV4):
    def _construct_header(self, checksum=ICMP_CHECKSUM):
        return struct.pack('BbHHh', ICMP_TYPE_IP6, ICMP_CODE, checksum,
                           ICMP_ID, ICMP_SEQ_NR+self.id)


    def unpack(self, packet):
        self.packet = packet
        self.header = self.packet[0:8]
        _type, code, chksum, _id, seqnr = struct.unpack("bbHHh", self.header)
        self.id = seqnr
        self.load = self.packet[16:53]

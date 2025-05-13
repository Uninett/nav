#
# Copyright (C) 23. Feb. 2004 - Lars Strand <lars strand at gnist org>
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
"""ICMP packet manipulation.

Required reading list:

* RFC  792 (ICMP)
* RFC 2460 (IPv6)
* RFC 4443 (ICMPv6)
* http://www.iana.org/assignments/icmpv6-parameters

"""

import struct
import array

ICMP_MINLEN = 8


class Packet(object):
    """An ICMP packet"""

    packet_slice = slice(0, None)
    header_slice = slice(0, 8)
    data_slice = slice(8, None)

    def __init__(self, packet=None, verify=True):
        """Initializes an ICMP packet structure.

        :param packet: Disassembled as an off -the-wire packet if supplied;
                       otherwise an empty ping packet is constructed.
        :param verify: Verify the packet checksum if True.

        """
        if packet:
            self._disassemble(packet, verify)
        else:
            self.type = getattr(self, 'ICMP_ECHO', 0)
            self.code = 0
            self.checksum = 0
            self.id = 0
            self.sequence = 0
            self.data = b''

    def __repr__(self):
        return "<ICMP %s type=%s code=%s id=%s sequence=%s>" % (
            self.__class__.__name__,
            self.lookup_type(),
            self.code,
            self.id,
            self.sequence,
        )

    def _disassemble(self, packet, verify=True):
        packet = packet[self.packet_slice]
        (self.type, self.code, self.checksum, self.id, self.sequence) = struct.unpack(
            "BBHHH", packet[self.header_slice]
        )
        self.data = packet[self.data_slice]

        if verify:
            my_checksum = inet_checksum(packet)
            if my_checksum != 0:
                raise ValueError("unable to verify packet checksum")

    def assemble(self, calc_checksum=True):
        """Assembles a raw ICMP packet string from packet attributes.

        :param calc_checksum: Calculate and fill the checksum field of the
                              packet if True.

        """
        packet = self._assemble(0)
        if calc_checksum:
            self.checksum = inet_checksum(packet)
            packet = self._assemble(self.checksum)
        return packet

    def _assemble(self, checksum):
        header = struct.pack(
            "BBHHH", self.type, self.code, checksum, self.id, self.sequence
        )
        packet = header + self.data
        return packet

    def lookup_type(self, type_=None):
        """Reverse looks up a packet type id and returns a name string.

        If the type is not known, the supplied integer is returned as a string
        instead.

        """
        if type_ is None:
            type_ = self.type
        attrs = vars(self.__class__)
        type_map = dict((v, k) for k, v in attrs.items() if k.startswith('ICMP_'))
        return type_map.get(type_, str(type_))


class PacketV4(Packet):
    """An ICMPv4 packet"""

    ICMP_ECHO_REPLY = 0
    ICMP_DESTINATION_UNREACHABLE = 3
    ICMP_ECHO = 8
    ICMP_TIME_EXCEEDED = 11

    # IPv4 RAW sockets include the IP header in the received datagram.  This
    # packet slice chops of the first 20 octets to get at the ICMP datagram
    packet_slice = slice(20, None)


class PacketV6(Packet):
    """An ICMPv6 packet.

    NOTE: This will never verify the checksum when disassembling a packet,
    since we need to generate a pseudo-header using the source and destination
    IPv6 addresses to include in the calculation of the sum.  See RFC 4443
    Section 2.3 and RFC 2460 Section 8.1.

    The generated checksum of an assembled PacketV6 will also likely be wrong
    because of this, but it appears that the OS somehow magically fixes the
    checksum when transmitted over the wire.

    """

    ICMP_DESTINATION_UNREACHABLE = 1
    ICMP_TIME_EXCEEDED = 3
    ICMP_ECHO = 128
    ICMP_ECHO_REPLY = 129

    ICMP_MULTICAST_LISTENER_QUERY = 130
    ICMP_MULTICAST_LISTENER_REPORT = 131
    ICMP_MULTICAST_LISTENER_DONE = 132

    ICMP_ROUTER_SOLICITATION = 133
    ICMP_ROUTER_ADVERTISEMENT = 134

    ICMP_NEIGHBOR_SOLICITATION = 135
    ICMP_NEIGHBOR_ADVERTISEMENT = 136

    def __init__(self, packet=None, verify=False):
        super(PacketV6, self).__init__(packet, False)


def inet_checksum(packet):
    """Calculates the checksum of a (ICMP) packet.

    RFC792 states: 'The 16 bit one's complement of the one's complement sum of
    all 16 bit words in the header.'

    Based on in_chksum found in ping.c on FreeBSD.
    """

    # add byte if not dividable by 2
    if len(packet) & 1:
        packet = packet + b'\0'

    # split into 16-bit word and insert into a binary array
    words = array.array('h', packet)
    sum_ = 0

    # perform ones complement arithmetic on 16-bit words
    for word in words:
        sum_ += word & 0xFFFF

    high = sum_ >> 16
    low = sum_ & 0xFFFF
    sum_ = high + low
    sum_ = sum_ + (sum_ >> 16)

    return (~sum_) & 0xFFFF  # return ones complement

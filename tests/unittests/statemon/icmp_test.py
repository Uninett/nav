from nav.statemon.icmppacket import PacketV6, PacketV4, inet_checksum
from unittest import TestCase
import os
from nav.statemon.megaping import Host

class ICMPPacketTestcase(TestCase):

    def test_assemble_v6_packet_echo(self):

        #Make packet
        packet = PacketV6()
        packet.data = 'Testing'
        packet.id = os.getpid()
        packet.sequence = 3
        packet = packet.assemble()

        #Make Packet object which disassembles the raw packet
        v6_packet = PacketV6(packet, False)

        #Check if ICMP_ECHO
        self.assertEquals(v6_packet.type, PacketV6.ICMP_ECHO)

        #Check sequence number
        self.assertEquals(v6_packet.sequence, 3)

        #Check payload
        self.assertEquals(v6_packet.data, 'Testing')

        #Check if Id of the packet is process id
        self.assertEquals(os.getpid(), v6_packet.id)

        #Check if the checksum is correct
        unpacked_packet = packet[v6_packet.packet_slice]
        self.assertEquals(inet_checksum(unpacked_packet), 0)

    def test_assemble_v4_packet_echo(self):

        #Make packet
        packet = PacketV4()
        packet.data = 'Testing'
        packet.id = os.getpid()
        packet.sequence = 3
        packet = packet.assemble()

        #Mocking the IP header and prepending it to the packet so disassembling of packet works
        IP_header = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        packet = IP_header + packet

        #Make Packet object which disassembles the raw packet
        v4_packet = PacketV4(packet, False)

        #Check if ICMP_ECHO
        self.assertEquals(v4_packet.type, PacketV4.ICMP_ECHO)

        #Check sequence number
        self.assertEquals(v4_packet.sequence, 3)

        #Check if Id of the packet is process id
        self.assertEquals(os.getpid(), v4_packet.id)

        #Check payload
        self.assertEquals(v4_packet.data, 'Testing')

        #Check if the checksum is correct
        unpacked_packet = packet[v4_packet.packet_slice]
        self.assertEquals(inet_checksum(unpacked_packet), 0)

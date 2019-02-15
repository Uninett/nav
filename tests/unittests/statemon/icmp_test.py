from nav.statemon.icmppacket import PacketV6, PacketV4, inet_checksum
from unittest import TestCase
import os


class ICMPPacketTestcase(TestCase):

    def test_assemble_v6_packet_echo(self):

        #Make packet
        packet = PacketV6()
        packet.data = b'Testing'
        packet.id = os.getpid()
        packet.sequence = 3
        packet = packet.assemble()

        #Make Packet object which disassembles the raw packet
        v6_packet = PacketV6(packet, False)

        #Check if ICMP_ECHO
        self.assertEqual(v6_packet.type, PacketV6.ICMP_ECHO)

        #Check sequence number
        self.assertEqual(v6_packet.sequence, 3)

        #Check payload
        self.assertEqual(v6_packet.data, b'Testing')

        #Check if Id of the packet is process id
        self.assertEqual(os.getpid(), v6_packet.id)

        #Check if the checksum is correct
        unpacked_packet = packet[v6_packet.packet_slice]
        self.assertEqual(inet_checksum(unpacked_packet), 0)

    def test_assemble_v4_packet_echo(self):

        #Make packet
        packet = PacketV4()
        packet.data = b'Testing'
        packet.id = os.getpid()
        packet.sequence = 3
        packet = packet.assemble()

        #Mocking the IP header and prepending it to the packet so disassembling of packet works
        IP_header = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        packet = IP_header + packet

        #Make Packet object which disassembles the raw packet
        v4_packet = PacketV4(packet, False)

        #Check if ICMP_ECHO
        self.assertEqual(v4_packet.type, PacketV4.ICMP_ECHO)

        #Check sequence number
        self.assertEqual(v4_packet.sequence, 3)

        #Check if Id of the packet is process id
        self.assertEqual(os.getpid(), v4_packet.id)

        #Check payload
        self.assertEqual(v4_packet.data, b'Testing')

        #Check if the checksum is correct
        unpacked_packet = packet[v4_packet.packet_slice]
        self.assertEqual(inet_checksum(unpacked_packet), 0)

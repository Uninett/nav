from nav.statemon.icmppacket import PacketV6, PacketV4, inet_checksum


class TestICMPPacket:
    def test_assemble_v6_packet_echo(self, modulo_pid):
        # Make packet
        packet = PacketV6()
        packet.data = b'Testing'
        packet.id = modulo_pid
        packet.sequence = 3
        packet = packet.assemble()

        # Make Packet object which disassembles the raw packet
        v6_packet = PacketV6(packet, False)

        # Check if ICMP_ECHO
        assert v6_packet.type == PacketV6.ICMP_ECHO

        # Check sequence number
        assert v6_packet.sequence == 3

        # Check payload
        assert v6_packet.data == b'Testing'

        # Check if Id of the packet is process id
        assert modulo_pid == v6_packet.id

        # Check if the checksum is correct
        unpacked_packet = packet[v6_packet.packet_slice]
        assert inet_checksum(unpacked_packet) == 0

    def test_assemble_v4_packet_echo(self, modulo_pid):
        # Make packet
        packet = PacketV4()
        packet.data = b'Testing'
        packet.id = modulo_pid
        packet.sequence = 3
        packet = packet.assemble()

        # Mocking the IP header and prepending it to the packet so disassembling of
        # packet works
        IP_header = b'\x00' * 20
        packet = IP_header + packet

        # Make Packet object which disassembles the raw packet
        v4_packet = PacketV4(packet, False)

        # Check if ICMP_ECHO
        assert v4_packet.type == PacketV4.ICMP_ECHO

        # Check sequence number
        assert v4_packet.sequence == 3

        # Check if Id of the packet is process id
        assert modulo_pid == v4_packet.id

        # Check payload
        assert v4_packet.data == b'Testing'

        # Check if the checksum is correct
        unpacked_packet = packet[v4_packet.packet_slice]
        assert inet_checksum(unpacked_packet) == 0

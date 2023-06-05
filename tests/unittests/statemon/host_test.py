from nav.statemon.megaping import Host
from nav.statemon.icmppacket import PacketV4, PacketV6


class TestHost:
    """Tests for the Host class"""

    def test_make_v4_packet(self, modulo_pid):
        """Test to make a v4 packet"""
        host = Host('127.0.0.1')
        assert not host.is_v6()

        assert host.packet
        assert isinstance(host.packet, PacketV4)

        packet, cookie = host.make_packet(64)

        assert packet
        assert cookie
        assert len(packet) == 64
        assert len(cookie) == 16

        assert host.packet.sequence == 0
        assert host.packet.id, modulo_pid

    def test_make_v6_packet(self, modulo_pid):
        """Test to make a v6 packet"""
        host = Host('2001:701::FFFF')
        assert host.is_v6()

        assert host.packet
        assert isinstance(host.packet, PacketV6)

        packet, cookie = host.make_packet(64)

        assert packet
        assert cookie
        assert len(packet) == 64
        assert len(cookie) == 16

        assert host.packet.sequence == 0
        assert host.packet.id == modulo_pid

    def test_ip_validation(self):
        """Test the IP valdidation helper methods for both v6 & v4"""
        assert Host('129.241.105.210').is_valid_ipv4()
        assert not Host('129.241.105.256').is_valid_ipv4()

        assert Host('2001:701::FFFF').is_valid_ipv6()
        assert not Host('127.0.0.1').is_valid_ipv6()

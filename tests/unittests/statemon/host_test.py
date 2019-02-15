from unittest import TestCase
import os
from nav.statemon.megaping import Host
from nav.statemon.icmppacket import PacketV4, PacketV6


class HostTestcase(TestCase):

    def test_make_v4_packet(self):
        """
        Test to make a v4 packet
        """
        host = Host('127.0.0.1')
        pid = os.getpid()
        self.assertFalse(host.is_v6())

        self.assertTrue(host.packet)
        self.assertTrue(isinstance(host.packet, PacketV4))

        packet, cookie = host.make_packet(64)

        self.assertTrue(packet)
        self.assertTrue(cookie)
        self.assertEqual(len(packet), 64)
        self.assertEqual(len(cookie), 16)

        self.assertEqual(host.packet.sequence, 0)
        self.assertEqual(host.packet.id, pid)

    def test_make_v6_packet(self):
        """
        Test to make a v6 packet
        """
        host = Host('2001:701::FFFF')
        pid = os.getpid()
        self.assertTrue(host.is_v6())

        self.assertTrue(host.packet)
        self.assertTrue(isinstance(host.packet, PacketV6))

        packet, cookie = host.make_packet(64)

        self.assertTrue(packet)
        self.assertTrue(cookie)
        self.assertEqual(len(packet), 64)
        self.assertEqual(len(cookie), 16)

        self.assertEqual(host.packet.sequence, 0)
        self.assertEqual(host.packet.id, pid)

    def test_ip_validation(self):
        """
        Test the IP valdidation helper methods for both v6 & v4
        """
        self.assertTrue(Host('129.241.105.210').is_valid_ipv4())
        self.assertFalse(Host('129.241.105.256').is_valid_ipv4())

        self.assertTrue(Host('2001:701::FFFF').is_valid_ipv6())
        self.assertFalse(Host('127.0.0.1').is_valid_ipv6())

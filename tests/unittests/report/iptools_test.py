from unittest import TestCase
from IPy import IP

from nav.report.IPtools import andIpMask


class IPtoolTest(TestCase):
    def test_ipv6_andIpMask(self):
        ip = IP('fe80:1234:5678:9012:a00:27ff:fe8e:df69')
        mask = IP('fe80:5678::/64')
        expected = IP('fe80:1230::/64')

        self.assertEqual(andIpMask(ip, mask), expected)

"""Basic tests for nav.arnold"""

import unittest
from nav.arnold import find_input_type


class TestArnold(unittest.TestCase):
    """Tests for nav.arnold"""

    def test_find_input_type(self):
        """Test find_input_type"""
        ip_address = '158.38.129.113'
        mac = '5c:f9:dd:78:72:8a'
        self.assertEqual(find_input_type(ip_address), 'IP')
        self.assertEqual(find_input_type(mac), 'MAC')
        self.assertEqual(find_input_type(123), 'SWPORTID')

    def test_typo_not_accepted(self):
        """Tests for weakness in IPy library"""
        ip_address = '158.38.129'
        self.assertEqual(find_input_type(ip_address), 'UNKNOWN')

    def test_end_on_zero(self):
        """Tests that IP-addresses that ends on zero are accepted"""
        ip_address = '158.38.129.0'
        self.assertEqual(find_input_type(ip_address), 'IP')

    def test_ipv6(self):
        """Tests that a simple ipv6 address is recognized"""
        ip_address = 'FE80:0000:0000:0000:0202:B3FF:FE1E:8329'
        self.assertEqual(find_input_type(ip_address), 'IP')

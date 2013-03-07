"""Basic tests for nav.arnold"""
import unittest
from nav.arnold import find_input_type

class TestArnold(unittest.TestCase):
    """Tests for nav.arnold"""

    def test_find_input_type(self):
        """Test find_input_type"""
        ip = '158.38.129.113'
        mac = '5c:f9:dd:78:72:8a'
        self.assertEqual(find_input_type(ip), 'IP')
        self.assertEqual(find_input_type(mac), 'MAC')
        self.assertEqual(find_input_type(123), 'SWPORTID')



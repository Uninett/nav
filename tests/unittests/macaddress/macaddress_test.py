#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import re
import unittest
from nav.macaddress import MacAddress

class MacAddressTest(unittest.TestCase):

    def test_mac_address_too_short(self):
        self.assertRaises(ValueError, MacAddress, "e4:2f")

    def test_mac_address_too_long(self):
        self.assertRaises(ValueError, MacAddress, "e4:2f:45:72:6e:76:01")

    def test_mac_address_too_small_integer_value(self):
        self.assertRaises(ValueError, MacAddress, 234)

    def test_mac_address_wrong_parameter_type_list(self):
        self.assertRaises(ValueError, MacAddress, [])

    def test_mac_address_wrong_parameter_type_dict(self):
        self.assertRaises(ValueError, MacAddress, {})

    def test_mac_address_address_contains_illegal_value(self):
        self.assertRaises(ValueError, MacAddress, "e4:2f:45:72:6e:o6")

    def test_mac_address_should_return_same_address_value_with_colon(self):
        param = 'e42f45726e76'
        mac_addr = MacAddress(param)
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:72:6e:76',
            "Return same address failed")

    def test_mac_address_return_same_address_value_with_colon(self):
        param = u'e4:2f:45:72:6e:76'
        mac_addr = MacAddress(param)
        self.assertEqual(unicode(mac_addr), param,
            "Return same colon-separated address failed")

    def test_mac_address_return_same_address_value_without_dash(self):
        param = 'e4-2f-45-72-6e-76'
        mac_addr = MacAddress(param)
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:72:6e:76',
            "Return same dash-separated address failed")

    def test_mac_address_return_same_address_value_without_dot(self):
        param = 'e42f.4572.6e76'
        mac_addr = MacAddress(param)
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:72:6e:76',
            "Return same dot-separated address failed")

    def test_mac_address_return_same_address_value_when_byte_string(self):
        param = b'\xe4\x2f\x45\x72\x6e\x76'
        mac_addr = MacAddress(MacAddress.from_octets(param))
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:72:6e:76',
            "Return same address when byte-string is parameter failed")

    def test_mac_address_with_colon_prefix_should_return_same_prefix(self):
        param = 'e4:2f:45:f'
        mac_addr = MacAddress(param)
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:f')

    def test_mac_address_with_dash_prefix_should_return_same_prefix(self):
        param = 'e4-2f-45-f'
        mac_addr = MacAddress(param)
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:f')

    def test_mac_address_with_dot_prefix_should_return_same_prefix(self):
        param = 'e42f.45f'
        mac_addr = MacAddress(param)
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:f')

    def test_mac_address_with_byte_string_prefix_should_return_zero_padded_addr(self):
        param = b'\xe4\x2f\x45\x72'
        mac_addr = MacAddress(MacAddress.from_octets(param))
        self.assertEqual(unicode(mac_addr), u'00:00:e4:2f:45:72')

    def test_mac_address_with_byte_string_prefix_should_return_same_address(self):
        param = b'\xe4\x2f\x45\x72\x6e\x76'
        mac_addr = MacAddress(MacAddress.from_octets(param))
        self.assertEqual(unicode(mac_addr), u'e4:2f:45:72:6e:76')

    def test_mac_address_to_string_without_delimiter_return_same_address(self):
        param = 'e42f.4572.6e76'
        mac_addr = MacAddress(param)
        self.assertEqual(mac_addr.to_string(), 'e42f45726e76')

    def test_mac_address_to_string_with_colon_delimiter_return_same_address(self):
        param = 'e4-2f-45-72-6e76'
        mac_addr = MacAddress(param)
        self.assertEqual(mac_addr.to_string(':'), 'e4:2f:45:72:6e:76')

    def test_mac_address_to_string_with_dash_delimiter_return_same_address(self):
        param = 'e42f.4572.6e76'
        mac_addr = MacAddress(param)
        self.assertEqual(mac_addr.to_string('-'), 'e4-2f-45-72-6e-76')

    def test_mac_address_to_string_with_dot_delimiter_return_same_address(self):
        param = 'e4:2f:45:72:6e:76'
        mac_addr = MacAddress(param)
        self.assertEqual(mac_addr.to_string('.'), 'e42f.4572.6e76')

    def test_mac_address_has_correct_length_with_full_length_address(self):
        param = 'e4:2f:45:72:6e:76'
        mac_addr = MacAddress(param)
        self.assertEqual(len(mac_addr), 1)

    def test_mac_address_has_correct_length_with_prefix_length_six(self):
        param = 'e4:2f:45'
        mac_addr = MacAddress(param)
        self.assertEqual(len(mac_addr), 16777216)

#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import unittest

from django.utils import six

from nav.macaddress import MacAddress, MacPrefix


class MacAddressTest(unittest.TestCase):

    def test_mac_address_too_short(self):
        self.assertRaises(ValueError, MacAddress, "e4:2f")

    def test_mac_address_too_long(self):
        self.assertRaises(ValueError, MacAddress, "e4:2f:45:72:6e:76:01")

    def test_mac_address_wrong_parameter_type_list(self):
        self.assertRaises(ValueError, MacAddress, [])

    def test_mac_address_wrong_parameter_type_dict(self):
        self.assertRaises(ValueError, MacAddress, {})

    def test_mac_address_address_contains_illegal_value(self):
        self.assertRaises(ValueError, MacAddress, "e4:2f:45:72:6e:o6")

    def test_mac_address_should_return_same_address_value_with_colon(self):
        param = 'e42f45726e76'
        mac_addr = MacAddress(param)
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:72:6e:76')

    def test_mac_address_mac_addres_as_parameter_should_return_same_address(self):
        param = 'e42f45726e76'
        ma = MacAddress(param)
        mac_addr = MacAddress(ma)
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:72:6e:76')

    def test_mac_address_return_same_address_value_with_colon(self):
        param = u'e4:2f:45:72:6e:76'
        mac_addr = MacAddress(param)
        self.assertEqual(six.text_type(mac_addr), param)

    def test_mac_address_return_same_address_value_without_dash(self):
        param = 'e4-2f-45-72-6e-76'
        mac_addr = MacAddress(param)
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:72:6e:76')

    def test_mac_address_return_same_address_value_without_dot(self):
        param = 'e42f.4572.6e76'
        mac_addr = MacAddress(param)
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:72:6e:76')

    def test_mac_address_return_same_address_value_when_byte_string(self):
        param = b'\xe4\x2f\x45\x72\x6e\x76'
        mac_addr = MacAddress(MacAddress.from_octets(param))
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:72:6e:76')

    def test_mac_address_with_byte_string_prefix_should_return_same_address(self):
        param = b'\xe4\x2f\x45\x72\x6e\x76'
        mac_addr = MacAddress(MacAddress.from_octets(param))
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:72:6e:76')

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

    def test_mac_address_param_as_int_should_return_same_in_hex(self):
        param = 11111110000
        mac_addr = MacAddress(param)
        self.assertEqual(six.text_type(mac_addr), u'00:02:96:46:15:70')

    def test_mac_addresses_are_equal(self):
        mac_addr1 = MacAddress('01:23:45:67:89:ab')
        mac_addr2 = MacAddress('01:23:45:67:89:ab')
        self.assertEqual(mac_addr1, mac_addr2)

    def test_mac_addresses_hash_the_same(self):
        mac_addr1 = MacAddress('01:23:45:67:89:ab')
        mac_addr2 = MacAddress('01:23:45:67:89:ab')
        self.assertEqual(hash(mac_addr1), hash(mac_addr2))

    def test_mac_addresses_hash_not_the_same(self):
        mac_addr1 = MacAddress('01:23:45:67:89:ab')
        mac_addr2 = MacAddress('01:23:45:67:89:ac')
        self.assertNotEqual(hash(mac_addr1), hash(mac_addr2))

    def test_mac_addresses_are_comparable(self):
        mac_addr1 = MacAddress('01:23:45:67:89:ab')
        mac_addr2 = MacAddress('01:23:45:67:89:cc')
        self.assertTrue(mac_addr1 < mac_addr2)
        self.assertTrue(mac_addr2 > mac_addr1)
        self.assertTrue(mac_addr1 <= mac_addr2)
        self.assertTrue(mac_addr2 >= mac_addr1)
        self.assertTrue(mac_addr1 != mac_addr2)

    def test_mac_address_should_compare_with_int(self):
        mac = MacAddress('01:23:45:67:89:ab')
        self.assertTrue(mac != 5)

    def test_mac_address_should_compare_with_string(self):
        mac = MacAddress('01:23:45:67:89:ab')
        self.assertTrue(mac == '01:23:45:67:89:ab')
        self.assertFalse(mac == 'blah')

    def test_mac_address_with_byte_string_prefix_should_return_zero_padded_addr(self):
        param = b'\xe4\x2f\x45\x72'
        mac_addr = MacAddress.from_octets(param)
        self.assertEqual(six.text_type(mac_addr), u'00:00:e4:2f:45:72')


class MacPrefixTest(unittest.TestCase):
    def test_macprefix_with_colon_prefix_should_return_same_prefix(self):
        param = 'e4:2f:45:f'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:f')

    def test_macprefix_with_dash_prefix_should_return_same_prefix(self):
        param = 'e4-2f-45-f'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:f')

    def test_macprefix_with_dot_prefix_should_return_same_prefix(self):
        param = 'e42f.45f'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr), u'e4:2f:45:f')

    def test_macprefix_should_return_zero_padded_when_address_start_with_zero(self):
        param = u'01:01:01'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr), u'01:01:01')

    def test_macprefix_should_return_zero_padded_when_address_start_with_5_zeros(self):
        param = u'00:00:01'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr), u'00:00:01')

    def test_macprefix_has_correct_length_with_prefix_length_six(self):
        param = 'e4:2f:45'
        mac_addr = MacPrefix(param)
        self.assertEqual(len(mac_addr), 16777216)

    def test_macprefix_has_correct_length_with_prefix_length_seven(self):
        param = u'e4-2f-45-3'
        mac_addr = MacPrefix(param)
        self.assertEqual(len(mac_addr), 1048576)

    def test_macprefix_has_correct_length_with_prefix_length_eigth(self):
        param = u'e42f.453d'
        mac_addr = MacPrefix(param)
        self.assertEqual(len(mac_addr), 65536)

    def test_macprefix_has_correct_length_with_full_length_address(self):
        param = 'e4:2f:45:72:6e:76'
        mac_addr = MacPrefix(param)
        self.assertEqual(len(mac_addr), 1)

    def test_macprefix_should_return_correct_value_with_zero_key(self):
        param = 'e42f.45'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr[0]), u'e4:2f:45:00:00:00')

    def test_macprefix_should_return_correct_value_with_key_equal_256(self):
        param = u'e4:2f:45:3d'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr[157]), u'e4:2f:45:3d:00:9d')

    def test_macprefix_should_return_correct_value_with_last_key(self):
        param = 'e4-2f-45'
        mac_addr = MacPrefix(param)
        self.assertEqual(six.text_type(mac_addr[-1]), u'e4:2f:45:ff:ff:ff')

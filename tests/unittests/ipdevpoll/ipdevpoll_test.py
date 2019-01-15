# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import unittest
import os
from random import shuffle
from IPy import IP

import django
django.setup()
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

from nav.models.manage import Prefix
from nav.ipdevpoll.utils import find_prefix, truncate_mac, binary_mac_to_hex, is_invalid_utf8


class UtilsTest(unittest.TestCase):
    def test_find_prefix(self):
        correct_ipv4 = IP('192.0.2.1')
        correct_ipv6 = IP('2001:db8:1234::1')

        loose_v6_prefix = Prefix(
            net_address='2001:db8::/32'
        )
        tight_v6_prefix = Prefix(
            net_address='2001:db8:1234::/48'
        )
        loose_v4_prefix = Prefix(
            net_address='192.0.2/24'
        )
        tight_v4_prefix = Prefix(
            net_address='192.0.2.0/26'
        )

        prefix_list = [
            loose_v6_prefix,
            tight_v6_prefix,
            loose_v4_prefix,
            tight_v4_prefix,
        ]
        shuffle(prefix_list)

        prefix1 = find_prefix(correct_ipv6, prefix_list)
        prefix2 = find_prefix(correct_ipv4, prefix_list)

        self.assertEqual(prefix1, tight_v6_prefix)
        self.assertEqual(prefix2, tight_v4_prefix)

    def test_binary_mac_to_hex(self):
        # Make a simple "binary" mac
        binary_mac = '123456'
        mac = '31:32:33:34:35:36'
        converted_mac = binary_mac_to_hex(binary_mac)
        self.assertEqual(converted_mac, mac)

    def test_truncate_mac(self):
        mac = '01:02:03:04:05:06'
        long_mac = mac + ':07:08:09'
        trunc_mac = truncate_mac(long_mac)
        self.assertEquals(trunc_mac, mac)

    def test_binary_mac_too_short(self):
        binary_mac = '23456'
        mac = '00:32:33:34:35:36'
        converted_mac = binary_mac_to_hex(binary_mac)
        self.assertEquals(converted_mac, mac)

    def test_binary_mac_too_long_should_return_last_part(self):
        binary_mac = 'x123456'
        mac = '31:32:33:34:35:36'
        converted_mac = binary_mac_to_hex(binary_mac)
        self.assertEquals(converted_mac, mac)

    def test_invalid_utf8(self):
        self.assertTrue(is_invalid_utf8(b'P%\xe4\xb8D\xb6\x108B\x1d'))

    def test_valid_utf8(self):
        self.assertFalse(is_invalid_utf8(b"ABC-123"))
        self.assertFalse(is_invalid_utf8(b'\xc3\x86\xc3\x98\xc3\x85'))

if __name__ == '__main__':
    unittest.main()

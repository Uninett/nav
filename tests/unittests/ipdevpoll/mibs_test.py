# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
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
from IPy import IP

os.environ['PYSNMP_API_VERSION'] = 'v3'
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.cisco_ietf_ip_mib import CiscoIetfIpMib

class IpMibTests(unittest.TestCase):
    def test_ipv4_syntax_with_length_should_be_parsed_correctly(self):
        ip_tuple = (1, 4, 192, 0L, 2L, 1L)
        expected = IP('192.0.2.1')
        ip = IpMib.inetaddress_to_ip(ip_tuple)
        self.assertEquals(ip, expected)

    def test_invalid_ipv4_syntax_should_raise_error(self):
        ip_tuple = (1, 4, 300, 300, 300, 300)
        self.assertRaises(ValueError, IpMib.inetaddress_to_ip, ip_tuple)

    def test_too_short_ipv4_address_should_raise_exception(self):
        ip_tuple = (1, 4, 1L, 2L)
        self.assertRaises(IndexToIpException, IpMib.inetaddress_to_ip, ip_tuple)

    def test_ipv4_syntax_not_annotated_with_size_should_parse_ok(self):
        ip_tuple = (1, 192, 0L, 2L, 1L)
        expected = IP('192.0.2.1')
        ip = IpMib.inetaddress_to_ip(ip_tuple)
        self.assertEquals(ip, expected)

    def test_too_long_ipv6_address_should_raise_exception(self):
        ip_tuple = (2, 16, 32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        self.assertRaises(IndexToIpException, IpMib.inetaddress_to_ip, ip_tuple)

    def test_ipv6_syntax_with_length_should_be_parsed_correctly(self):
        ip_tuple = (2, 16, 32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        expected = IP('2001:db8:1234::1')
        ip = IpMib.inetaddress_to_ip(ip_tuple)
        self.assertEquals(ip, expected)

class Ipv6MibTests(unittest.TestCase):
    def test_ipv6mib_index(self):
        ip_tuple = (32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        expected = IP('2001:db8:1234::1')
        ip = Ipv6Mib.ipv6address_to_ip(ip_tuple)
        self.assertEquals(ip, expected)

if __name__ == '__main__':
    unittest.main()


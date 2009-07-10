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
from IPy import IP

import os
os.environ['PYSNMP_API_VERSION'] = 'v3'
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'
from nav.ipdevpoll.plugins.arp import *

class ArpPluginTest(unittest.TestCase):
    def test_ipmib_index(self):
        correct_ip = IP('127.0.0.1')

        # This is what we expect, ifIndex + IP
        ip_tuple = (1L, 127L, 0L, 0L, 1L)
        ip = ipmib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ip)

        # Three other things, but the four last are still an IP, should work
        # fine.
        ip_tuple = (1, 2, 3, 127, 0, 0, 1)
        ip = ipmib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ip)

        # Just IP
        ip_tuple = (127L, 0L, 0L, 1L)
        ip = ipmib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ip)

        # To few parts, should fail
        ip_tuple = (1L, 2L, 3L)
        self.assertRaises(Exception, ipmib_index_to_ip, ip_tuple)

    def test_ipv6mib_index(self):
        correct_ip = IP('2001:db8::1')

        # This is what we expect, ifIndex + IP
        ip_tuple = (1L, 32L, 1L, 13L, 184L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        ip = ipv6mib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ip)

        # Three other things, but the last 16 parts are still an IP, should
        # work fine.
        ip_tuple = (1, 2, 3, 32, 1, 13, 184, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
        ip = ipv6mib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ip)

        # Just an IP
        ip_tuple = (32L, 1L, 13L, 184L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        ip = ipv6mib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ip)

        # To few parts, should fail
        ip_tuple = (1L, 2L, 3L)
        self.assertRaises(Exception, ipv6mib_index_to_ip, ip_tuple)

    def test_ciscomib_index(self):
        correct_ipv4 = IP('127.0.0.1')
        correct_ipv6 = IP('2001:db8::1')

        ip_tuple = (1L, 2L, 16L, 32L, 1L, 13L, 184L, 0L, 0L, 0L, 0L, 0L, 0L,
                    0L, 0L, 0L, 0L, 0L, 1L)
        ip = ciscomib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ipv6)

        ip_tuple = (1L, 1L, 16L, 32L, 1L, 13L, 184L, 0L, 0L, 0L, 0L, 0L, 0L,
                    0L, 0L, 0L, 0L, 0L, 1L)
        self.assertRaises(Exception, ciscomib_index_to_ip, ip_tuple)

        ip_tuple = (1L, 1L, 4L, 127L, 0L, 0L, 1L)
        ip = ciscomib_index_to_ip(ip_tuple)
        self.assertEquals(ip, correct_ipv4)

        ip_tuple = (1L, 2L, 4L, 127L, 0L, 0L, 1L)
        self.assertRaises(Exception, ciscomib_index_to_ip, ip_tuple)

if __name__ == '__main__':
    unittest.main()

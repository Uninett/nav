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

os.environ['PYSNMP_API_VERSION'] = 'v3'
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

from IPy import IP

from nav.models.manage import Prefix
from nav.ipdevpoll.plugins.arp import *

class ArpPluginTest(unittest.TestCase):
    def setUp(self):
        self.correct_ipv4 = IP('192.0.2.1')
        self.correct_ipv6 = IP('2001:db8:1234::1')

    def test_ipmib_index(self):
        # This is what we expect, ifIndex + IP
        ip_tuple = (1L, 192, 0L, 2L, 1L)
        ip = ipmib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv4)

        # Three other things, but the four last are still an IP, should work
        # fine.
        ip_tuple = (1, 2, 3, 192, 0, 2, 1)
        ip = ipmib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv4)

        # Just IP
        ip_tuple = (192, 0L, 2L, 1L)
        ip = ipmib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv4)

        # To few parts, should fail
        ip_tuple = (1L, 2L, 3L)
        self.assertRaises(IndexToIpException, ipmib_index_to_ip, ip_tuple)

    def test_ipv6mib_index(self):
        # This is what we expect, ifIndex + IP
        ip_tuple = (1L, 32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        ip = ipv6mib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv6)

        # Three other things, but the last 16 parts are still an IP, should
        # work fine.
        ip_tuple = (1, 2, 3, 32, 1, 13, 184, 18, 52, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1)
        ip = ipv6mib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv6)

        # Just an IP
        ip_tuple = (32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        ip = ipv6mib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv6)

        # To few parts, should fail
        ip_tuple = (1L, 2L, 3L)
        self.assertRaises(IndexToIpException, ipv6mib_index_to_ip, ip_tuple)

    def test_ciscomib_index(self):
        ip_tuple = (1L, 2L, 16L, 32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L,
                    0L, 0L, 0L, 0L, 0L, 1L)
        ip = ciscomib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv6)

        ip_tuple = (1L, 1L, 16L, 32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L,
                    0L, 0L, 0L, 0L, 0L, 1L)
        self.assertRaises(IndexToIpException, ciscomib_index_to_ip, ip_tuple)

        ip_tuple = (1L, 1L, 4L, 192, 0L, 2L, 1L)
        ip = ciscomib_index_to_ip(ip_tuple)
        self.assertEquals(ip, self.correct_ipv4)

        ip_tuple = (1L, 2L, 4L, 192, 0L, 2L, 1L)
        self.assertRaises(IndexToIpException, ciscomib_index_to_ip, ip_tuple)

    def test_find_prefix(self):
        loose_prefix = Prefix(
            net_address='2001:db8::/32'
        )
        tight_prefix = Prefix(
            net_address='2001:db8:1234::/48'
        )

        prefix1 = find_prefix(self.correct_ipv6, [loose_prefix, tight_prefix])
        prefix2 = find_prefix(self.correct_ipv6, [tight_prefix, loose_prefix])

        self.assertEqual(prefix1, tight_prefix)
        self.assertEqual(prefix2, tight_prefix)

        loose_prefix = Prefix(
            net_address='192.0.2/24'
        )
        tight_prefix = Prefix(
            net_address='192.0.2.0/26'
        )

        prefix1 = find_prefix(self.correct_ipv4, [loose_prefix, tight_prefix])
        prefix2 = find_prefix(self.correct_ipv4, [tight_prefix, loose_prefix])

        self.assertEqual(prefix1, tight_prefix)
        self.assertEqual(prefix2, tight_prefix)

if __name__ == '__main__':
    unittest.main()

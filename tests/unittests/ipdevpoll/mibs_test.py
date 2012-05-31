#
# Copyright (C) 2008, 2009, 2011 UNINETT AS
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

from twisted.internet import defer
from twisted.python import failure

from minimock import Mock

os.environ['PYSNMP_API_VERSION'] = 'v3'
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.cisco_ietf_ip_mib import CiscoIetfIpMib
from nav.mibs.entity_mib import EntityMib
from nav.mibs.snmpv2_mib import Snmpv2Mib

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

    def test_ipv4_prefix_rowpointer_should_be_parsed_correctly(self):
        rowpointer = (1, 3, 6, 1, 2, 1, 4, 32, 1, 5, 439541760, 1, 4, 192, 168, 70, 0, 24)
        expected = IP('192.168.70/24')
        prefix = IpMib.prefix_index_to_ip(rowpointer)
        self.assertEquals(prefix, expected)

    def test_ipv6_prefix_rowpointer_should_be_parsed_correctly(self):
        rowpointer = (1, 3, 6, 1, 2, 1, 4, 32, 1, 5, 11, 2, 16, 32, 1, 7, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64)
        expected = IP('2001:700:0:500::/64')
        prefix = IpMib.prefix_index_to_ip(rowpointer)
        self.assertEquals(prefix, expected)

class Ipv6MibTests(unittest.TestCase):
    def test_ipv6mib_index(self):
        ip_tuple = (32L, 1L, 13L, 184L, 18L, 52L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 1L)
        expected = IP('2001:db8:1234::1')
        ip = Ipv6Mib.ipv6address_to_ip(ip_tuple)
        self.assertEquals(ip, expected)

class EntityMibTests(unittest.TestCase):
    def test_empty_logical_type_should_not_raise(self):
        mib = EntityMib(Mock('AgentProxy'))
        def mock_retrieve(columns):
            return defer.succeed(
                {1: {'entLogicalDescr': None,
                     'entLogicalType': None,
                     'entLogicalCommunity': None}}
                )

        mib.retrieve_columns = mock_retrieve
        df = mib.retrieve_alternate_bridge_mibs()
        self.assertTrue(df.called)
        if isinstance(df.result, failure.Failure):
            df.result.raiseException()

class Snmpv2MibTests(unittest.TestCase):
    def test_simple_uptime_deviation_should_be_correct(self):
        first_uptime =  (1338372778.0, 10000L)
        second_uptime = (1338372900.0, 22200L)
        dev = Snmpv2Mib.get_uptime_deviation(first_uptime, second_uptime)
        self.assertTrue(abs(dev) < 0.5,
                        msg="deviation is higher than 0.5: %r" % dev)

    def test_wrapped_uptime_deviation_should_be_correct(self):
        first_uptime =  (1338372778.0, 4294967196L)
        second_uptime = (1338372900.0, 12100L)
        dev = Snmpv2Mib.get_uptime_deviation(first_uptime, second_uptime)
        self.assertTrue(abs(dev) < 0.5,
                        msg="deviation is higher than 0.5: %r" % dev)

if __name__ == '__main__':
    unittest.main()


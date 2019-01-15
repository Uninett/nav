# Copyright (C) 2009 Uninett AS
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

from nav import util
from nav.util import IPRange
from IPy import IP


class UtilTestCase(unittest.TestCase):
    """Test various functions in the util module"""
    def setUp(self):
        self.gradient_start = 0
        self.gradient_stop = 952
        self.gradient_steps = 20
        self.gradient = util.gradient(self.gradient_start,
                                      self.gradient_stop,
                                      self.gradient_steps)
        self.reverse_gradient = util.gradient(self.gradient_stop,
                                              self.gradient_start,
                                              self.gradient_steps)

    def test_gradient_size(self):
        self.assertEquals(self.gradient_steps, len(self.gradient))

    def test_gradient_end_points(self):
        self.assertEquals(self.gradient_start, self.gradient[0])
        self.assertEquals(self.gradient_stop, self.gradient[-1])

    def test_gradient_order(self):
        ordered = sorted(self.gradient)
        self.assertEquals(ordered, self.gradient)

        ordered = sorted(self.reverse_gradient)
        ordered.reverse()
        self.assertEquals(ordered, self.reverse_gradient)

    def test_colortohex(self):
        self.assertEquals('ea702a', util.colortohex((234, 112, 42)))

    def test_is_valid_ip(self):
        valid_ips = ['129.241.75.1', '10.0.25.62', '2001:700:1::abcd',
                     'fe80::baad']
        invalid_ips = ['www.uninett.no', '92835235', '5:4', '-5325']

        for ip in valid_ips:
            self.assert_(util.is_valid_ip(ip),
                         msg="%s should be valid" % ip)

        for ip in invalid_ips:
            self.assertFalse(util.is_valid_ip(ip),
                             msg="%s should be invalid" % ip)


class IPRangeTests(unittest.TestCase):
    def test_ipv4_range_length_should_be_correct(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        self.assertEquals(len(i), 128)

    def test_ipv6_range_length_should_be_correct(self):
        i = IPRange(IP('fe80:700:1::'), IP('fe80:700:1::f'))
        self.assertEquals(len(i), 16)

    def test_indexed_access_should_work(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        self.assertEquals(i[5], IP('10.0.42.5'))

    def test_out_of_bounds_positive_index_should_raise(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        self.assertRaises(IndexError, lambda x: i[x], 129)

    def test_out_of_bounds_negative_index_should_raise(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        self.assertRaises(IndexError, lambda x: i[x], -129)


class IPRangeStringTests(unittest.TestCase):
    def test_simple_ipv4_range_should_parse(self):
        i = IPRange.from_string('10.0.42.0-10.0.42.63')
        self.assertEquals(i[0], IP('10.0.42.0'))
        self.assertEquals(i[-1], IP('10.0.42.63'))

    def test_simple_ipv6_range_should_parse(self):
        i = IPRange.from_string('fe80:700:1::-fe80:700:1::f')
        self.assertEquals(i[0], IP('fe80:700:1::'))
        self.assertEquals(i[-1], IP('fe80:700:1::f'))

    def test_assembled_ipv4_range_should_parse(self):
        i = IPRange.from_string('10.0.42.0-127')
        self.assertEquals(i[0], IP('10.0.42.0'))
        self.assertEquals(i[-1], IP('10.0.42.127'))

    def test_assembled_ipv6_range_should_parse(self):
        i = IPRange.from_string('fe80:700:1::aaa-fff')
        self.assertEquals(i[0], IP('fe80:700:1::aaa'))
        self.assertEquals(i[-1], IP('fe80:700:1::fff'))

    def test_ipv4_subnet_should_parse(self):
        i = IPRange.from_string('10.0.99.0/24')
        self.assertEquals(i[0], IP('10.0.99.0'))
        self.assertEquals(i[-1], IP('10.0.99.255'))

    def test_ipv4_short_subnet_should_parse(self):
        i = IPRange.from_string('10.0.99/24')
        self.assertEquals(i[0], IP('10.0.99.0'))
        self.assertEquals(i[-1], IP('10.0.99.255'))

    def test_ipv4_with_unspecified_mask_should_parse(self):
        i = IPRange.from_string('192.168.63/')
        self.assertTrue(len(i) > 1)

    def test_ipv6_with_unspecified_mask_should_parse(self):
        i = IPRange.from_string('fe80:800:1::/')
        self.assertTrue(i.len() > 1)

    def test_range_with_no_end_should_raise(self):
        self.assertRaises(ValueError, IPRange.from_string, '10.0.42.0-')

    def test_garbage_range_should_raise(self):
        self.assertRaises(ValueError, IPRange.from_string, 'blapp')

    def test_empty_range_should_raise(self):
        self.assertRaises(ValueError, IPRange.from_string, '')

    def test_invalid_netmask_should_raise(self):
        self.assertRaises(ValueError, IPRange.from_string, '10.0.0.0/2000')

    def test_multi_range_should_raise(self):
        self.assertRaises(ValueError,
                          IPRange.from_string, '10.0.0.0-10.0.1.0-42')

    def test_multi_mask_should_raise(self):
        self.assertRaises(ValueError, IPRange.from_string, '10.0.0.0/8/24')

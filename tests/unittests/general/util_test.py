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
import pytest

from nav import util
from nav.util import IPRange, first_true
from IPy import IP


class TestGradient(object):
    """tests for the gradient function"""

    gradient_start = 0
    gradient_stop = 952
    gradient_steps = 20
    gradient = util.gradient(gradient_start, gradient_stop, gradient_steps)
    reverse_gradient = util.gradient(gradient_stop, gradient_start, gradient_steps)

    def test_gradient_size(self):
        assert self.gradient_steps == len(self.gradient)

    def test_gradient_end_points(self):
        assert self.gradient_start == self.gradient[0]
        assert self.gradient_stop == self.gradient[-1]

    def test_gradient_order(self):
        ordered = sorted(self.gradient)
        assert ordered == self.gradient

        ordered = sorted(self.reverse_gradient)
        ordered.reverse()
        assert ordered == self.reverse_gradient


def test_colortohex():
    assert 'ea702a' == util.colortohex((234, 112, 42))


def test_is_valid_ip():
    valid_ips = ['129.241.75.1', '10.0.25.62', '2001:700:1::abcd', 'fe80::baad']
    invalid_ips = ['www.uninett.no', '92835235', '5:4', '-5325']

    for ip in valid_ips:
        assert util.is_valid_ip(ip), "%s should be valid" % ip

    for ip in invalid_ips:
        assert not util.is_valid_ip(ip), "%s should be invalid" % ip


class TestIPRange(object):
    def test_ipv4_range_length_should_be_correct(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        assert len(i) == 128

    def test_ipv6_range_length_should_be_correct(self):
        i = IPRange(IP('fe80:700:1::'), IP('fe80:700:1::f'))
        assert len(i) == 16

    def test_indexed_access_should_work(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        assert i[5] == IP('10.0.42.5')

    def test_out_of_bounds_positive_index_should_raise(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        with pytest.raises(IndexError):
            i[129]

    def test_out_of_bounds_negative_index_should_raise(self):
        i = IPRange(IP('10.0.42.0'), IP('10.0.42.127'))
        with pytest.raises(IndexError):
            i[-129]


class TestIPRangeString(object):
    def test_simple_ipv4_range_should_parse(self):
        i = IPRange.from_string('10.0.42.0-10.0.42.63')
        assert i[0] == IP('10.0.42.0')
        assert i[-1] == IP('10.0.42.63')

    def test_simple_ipv6_range_should_parse(self):
        i = IPRange.from_string('fe80:700:1::-fe80:700:1::f')
        assert i[0] == IP('fe80:700:1::')
        assert i[-1] == IP('fe80:700:1::f')

    def test_assembled_ipv4_range_should_parse(self):
        i = IPRange.from_string('10.0.42.0-127')
        assert i[0] == IP('10.0.42.0')
        assert i[-1] == IP('10.0.42.127')

    def test_assembled_ipv6_range_should_parse(self):
        i = IPRange.from_string('fe80:700:1::aaa-fff')
        assert i[0] == IP('fe80:700:1::aaa')
        assert i[-1] == IP('fe80:700:1::fff')

    def test_ipv4_subnet_should_parse(self):
        i = IPRange.from_string('10.0.99.0/24')
        assert i[0] == IP('10.0.99.0')
        assert i[-1] == IP('10.0.99.255')

    def test_ipv4_short_subnet_should_parse(self):
        i = IPRange.from_string('10.0.99/24')
        assert i[0] == IP('10.0.99.0')
        assert i[-1] == IP('10.0.99.255')

    def test_ipv4_with_unspecified_mask_should_parse(self):
        i = IPRange.from_string('192.168.63/')
        assert len(i) > 1

    def test_ipv6_with_unspecified_mask_should_parse(self):
        i = IPRange.from_string('fe80:800:1::/')
        assert i.len() > 1

    def test_range_with_no_end_should_raise(self):
        with pytest.raises(ValueError):
            IPRange.from_string('10.0.42.0-')

    def test_garbage_range_should_raise(self):
        with pytest.raises(ValueError):
            IPRange.from_string('blapp')

    def test_empty_range_should_raise(self):
        with pytest.raises(ValueError):
            IPRange.from_string('')

    def test_invalid_netmask_should_raise(self):
        with pytest.raises(ValueError):
            IPRange.from_string('10.0.0.0/2000')

    def test_multi_range_should_raise(self):
        with pytest.raises(ValueError):
            IPRange.from_string('10.0.0.0-10.0.1.0-42')

    def test_multi_mask_should_raise(self):
        with pytest.raises(ValueError):
            IPRange.from_string('10.0.0.0/8/24')


class TestFirstTrue(object):
    def test_first_true_should_find_true_element(self):
        elems = [False, False, True, False]
        assert first_true(elems) is True

    def test_first_true_should_return_default_value_when_no_true_found(self):
        elems = [False, False, False]
        default = object()
        assert first_true(elems, default=default) is default

    def test_first_true_should_parse_predicate_correctly(self):
        elems = ["foo", "bar", "baz", "frobnicate"]
        assert first_true(elems, pred=lambda x: x == "baz") == "baz"

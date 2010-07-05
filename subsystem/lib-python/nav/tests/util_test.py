# Copyright (C) 2009 UNINETT AS
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
import unittest

from nav import util

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

    def test_isValidIP(self):
        valid_ips = ['129.241.75.1', '10.0.25.62', '2001:700:1::abcd',
                     'fe80::baad']
        invalid_ips = ['www.uninett.no', '92835235', '5:4', '-5325']

        for ip in valid_ips:
            self.assert_(util.isValidIP(ip),
                         msg="%s should be valid" % ip)

        for ip in invalid_ips:
            self.assertFalse(util.isValidIP(ip),
                             msg="%s should be invalid" % ip)

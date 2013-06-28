#
# Copyright (C) 2013 UNINETT AS
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
"""Tests for metrics.lookups module"""

import unittest
from nav.metrics.lookups import (device_reverse, interface_reverse,
                                 prefix_reverse, shorten)
from nav.models.manage import Netbox, Interface, Prefix

# TODO: Useless tests, need to use mock
class TestLookups(unittest.TestCase):

    def setUp(self):
        self.device_metric = "nav.devices.buick_lab_uninett_no.ports.1.ifInOctets"
        self.prefix_metric = "nav.prefixes.158_38_130_0_25.ip_range"

    def test_device_reverse(self):
        result = device_reverse([self.device_metric])
        self.assertEqual(result[self.device_metric],
                         Netbox.objects.get(sysname='buick.lab.uninett.no'))

    def test_interface_reverse(self):
        result = interface_reverse([self.device_metric])
        self.assertEqual(result[self.device_metric],
                         Interface.objects.get(pk=4006))

    def test_prefix_reverse(self):
        result = prefix_reverse([self.prefix_metric])
        self.assertEqual(result[self.prefix_metric],
                         Prefix.objects.get(net_address='158.38.130.0/25'))

    def test_shorten(self):
        self.assertEqual(shorten(self.device_metric, 3),
                         "nav.devices.buick_lab_uninett_no")

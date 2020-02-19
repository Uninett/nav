#
# Copyright (C) 2013 Uninett AS
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
"""Tests for snmp_utils"""

import unittest

from nav.portadmin.snmp.base import SNMPHandler
from nav.bitvector import BitVector


class SnmpUtilsTest(unittest.TestCase):
    """Tests for snmp_utils"""

    def test_chunkify(self):
        vlans = [10, 33, 513, 1023, 1025, 2048, 4095]
        b = BitVector(512 * b'\000')
        for vlan in vlans:
            b[vlan] = 1

        self.assertEqual(b.get_set_bits(), vlans)
        first, second, third, fourth = SNMPHandler._chunkify(b, 4)

        self.assertEqual(first.get_set_bits(), [10, 33, 513, 1023])
        self.assertEqual(second.get_set_bits(), [1])
        self.assertEqual(third.get_set_bits(), [0])
        self.assertEqual(fourth.get_set_bits(), [1023])

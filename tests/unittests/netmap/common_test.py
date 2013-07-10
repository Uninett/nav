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

import unittest
from mock import Mock
from nav.netmap.metadata import edge_metadata, edge_to_json
from nav.netmap.topology import NetmapEdge
from topology_testcase import TopologyTestCase

class NetmapCommonTests(TopologyTestCase):

    def test_ordered_set_length_is_correct_where__a_b__is_same_as__b_a(self):
        foo = set()
        foo.add(NetmapEdge((self.a1, self.b1)))
        foo.add(NetmapEdge((self.b1, self.a1)))
        self.assertEqual(1, len(foo))
        foo.add(NetmapEdge((self.a3, self.c3)))
        self.assertEqual(2, len(foo))

    def get_item_from_netmapedge_successfull_even_if_opposite_order(self):
        foo = set()
        foo.add(NetmapEdge((self.a1, self.b1)))
        self.assertTrue((self.b1, self.a1) in foo)
        self.assertTrue(foo[(self.b1, self.a1)])




if __name__ == '__main__':
    unittest.main()
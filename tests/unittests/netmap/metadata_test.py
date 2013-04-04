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


class NetmapMetadataTests(unittest.TestCase):

    def test_not_failing_when_both_interface_speed_is_undefined(self):
        netbox_a = Mock('Netbox')
        netbox_b = Mock('Netbox')
        results = edge_metadata(netbox_a,  None, netbox_b, None)
        self.assertIsNone(results['link_speed'])

    def test_json_edge_is_NA_if_speed_is_undefined(self):
        netbox_a = Mock('Netbox')
        netbox_b = Mock('Netbox')
        results = edge_to_json(edge_metadata(netbox_a, None, netbox_b, None))
        self.assertEquals(results['link_speed'], 'N/A')

if __name__ == '__main__':
    unittest.main()
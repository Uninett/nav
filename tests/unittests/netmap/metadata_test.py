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
from nav.models.manage import Netbox, Room, Location, SwPortVlan, Vlan
from nav.models.profiles import NetmapViewNodePosition
from nav.netmap import stubs, metadata
from nav.netmap.metadata import edge_metadata, edge_to_json
from topology_testcase import TopologyTestCase

class NetworkXMetadataTests(TopologyTestCase):
    def setUp(self):
        super(NetworkXMetadataTests, self).setUp()
        self._setupNetmapGraph()

    def test_node_a1_and_b1_contains_vlan_metadata(self):
        vlans = self.netmap_graph.node[self.a]['metadata']['vlans']

        self.assertEqual(1, len(vlans))
        self.assertEqual(vlans[0][1], self.vlan__a1_b1)
        # nav_vlan_id == SwPortVlan.Vlan.Id
        self.assertEqual(vlans[0][0], self.vlan__a1_b1.vlan.id)

    def test_edge_between_a_and_b_has_2_edges_as_metdata(self):
        edge_meta = self.netmap_graph.get_edge_data(self.a, self.b)['meta']
        self.assertEqual(2, len(edge_meta))

    def test_edge_between_a_and_b_contains_a1_b1__and__a2_b2_uplinks(self):
        edge_meta = [x['uplink'] for x in
                     self.netmap_graph.get_edge_data(self.a, self.b)['meta']]
        self.assertEqual(self.a1, edge_meta[0]['thiss']['interface'])
        self.assertEqual(self.b1, edge_meta[0]['other']['interface'])
        self.assertEqual(self.a2, edge_meta[1]['thiss']['interface'])
        self.assertEqual(self.b2, edge_meta[1]['other']['interface'])


class JsonMetadataTests(TopologyTestCase):

    def setUp(self):
        super(JsonMetadataTests, self).setUp()
        self.room = Room()
        self.room.id = 'Pegasus'
        self.room.description = 'room description'
        self.room.location = Location()
        self.room.location.id = 'galaxy'
        self.room.location.description = 'In a galaxy far far away'
        self.a = Netbox()
        self.a.id = 999
        self.a.sysname = 'foo.nav.unittest'
        self.a.room = self.room
        self.a.category_id = 'GW'
        self.a.ip = '::1'

        a_position = NetmapViewNodePosition()
        a_position.x = 1.3
        a_position.y = 3.7
        self.nx_edge_metadata = {'metadata': {
            'position': a_position
        }}
        self.nx_node_metadata = {'metadata': {
            'vlans': [(1337, SwPortVlan(id=1231, interface=self.a1, vlan=Vlan(id=1337, vlan=10, net_ident='unittest vlan')))]
        }}



    def test_not_failing_when_both_interface_speed_is_undefined(self):
        netbox_a = Mock('Netbox')
        netbox_b = Mock('Netbox')
        results = edge_metadata(netbox_a,  None, netbox_b, None)
        self.assertTrue(results['link_speed'] is None)

    def test_json_edge_is_NA_if_speed_is_undefined(self):
        netbox_a = Mock('Netbox')
        netbox_b = Mock('Netbox')
        results = edge_to_json(edge_metadata(netbox_a, None, netbox_b, None))
        self.assertEquals(results['link_speed'], 'N/A')

    def test_stubbed_netbox_always_gives_is_elink(self):
        netbox = stubs.Netbox()
        netbox.sysname = 'IamStub'
        netbox.category_id = 'ELINK'
        self.assertEqual({
            'category': 'ELINK',
            'is_elink_node': True,
            'sysname': 'IamStub'
        }, metadata._node_to_json(netbox, self.nx_edge_metadata))

    def test_json_id_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('id' in foo)
        self.assertEqual('999', foo['id'])

    def test_json_sysname_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('sysname' in foo)
        self.assertEqual('foo.nav.unittest', foo['sysname'])

    def test_json_category_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('category' in foo)
        self.assertEqual('GW', foo['category'])

    def test_json_ip_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('ip' in foo)
        self.assertEqual('::1', foo['ip'])

    def test_json_ipdevinfo_link_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('ipdevinfo_link' in foo)
        self.assertEqual('/ipdevinfo/foo.nav.unittest/', foo['ipdevinfo_link'])

    def test_json_position_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('position' in foo)
        self.assertEqual({'x': 1.3, 'y': 3.7}, foo['position'])

    def test_json_position_is_none_if_not_available_in_metadata_from_node(self):
        del self.nx_edge_metadata['metadata']['position']
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('position' in foo)
        self.assertIsNone(foo['position'])

    def test_json_up_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('up' in foo)
        self.assertEqual('y', foo['up'])

    def test_json_up_image_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('up_image' in foo)
        self.assertEqual('green.png', foo['up_image'])

    def test_json_roomid_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('roomid' in foo)
        self.assertEqual('Pegasus', foo['roomid'])

    def test_json_locationid_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('locationid' in foo)
        self.assertEqual('galaxy', foo['locationid'])

    def test_json_location_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('location' in foo)
        self.assertEqual('In a galaxy far far away', foo['location'])

    def test_json_room_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('room' in foo)
        self.assertEqual(u'Pegasus (room description)', foo['room'])

    def test_json_is_elink_node_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('is_elink_node' in foo)
        self.assertFalse(foo['is_elink_node'])

    def test_json_node_contains_vlan_data(self):
        foo = metadata.node_to_json_layer2(self.a, self.nx_node_metadata)
        self.assertTrue('vlans' in foo)
        self.assertEqual(1, len(foo['vlans']))

        # nav_vlan_id (key) should equal swpv.vlan.id
        self.assertEqual(
            self.nx_node_metadata.get('metadata')['vlans'][0][0],
            self.nx_node_metadata.get('metadata')['vlans'][0][1].vlan.id
        )

        self.assertEqual(1337, foo['vlans'][0]['nav_vlan'])
        self.assertEqual(10, foo['vlans'][0]['vlan'])
        # nav_vlan_id == swpv.vlan.id


if __name__ == '__main__':
    unittest.main()
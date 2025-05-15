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

import unittest
from nav.models.manage import SwPortVlan, Vlan
from nav.models.profiles import NetmapViewNodePosition
from nav.netmap import stubs, metadata
from nav.netmap.metadata import Edge, Group
from .metaclass_testcase import MetaClassTestCase
from .topology_layer3_testcase import TopologyLayer3TestCase
from .topology_layer2_testcase import TopologyLayer2TestCase


class MetaClassesJsonTests(MetaClassTestCase):
    def test_allow_group_interface_to_be_none(self):
        json = Group(self.netbox).to_json()
        self.assertFalse('interface' in json['netbox'])

    def test_group_renders_gw_ip_if_included(self):
        assert self.netbox is not None
        group = Group(self.netbox)
        group.gw_ip = '192.168.42.254'
        json = group.to_json()
        self.assertTrue('gw_ip' in json)
        self.assertEqual('192.168.42.254', json['gw_ip'])

    def test_group_renders_virtual_if_included_and_value_is_true(self):
        group = Group(self.netbox)
        group.virtual = True
        json = group.to_json()
        self.assertTrue('virtual' in json)
        self.assertEqual(True, json['virtual'])

    def test_group_renders_virtual_if_included_and_value_is_false(self):
        group = Group(self.netbox)
        group.virtual = False
        json = group.to_json()
        self.assertTrue('virtual' in json)
        self.assertEqual(False, json['virtual'])


class SharedJsonMetadataTests:
    def test_not_failing_when_both_interface_speed_is_undefined(self):
        self.a1.speed = None
        self.b1.speed = None
        results = Edge((self.a, self.b), (self.a1, self.b1))
        self.assertTrue(results.link_speed is None)

    def test_json_edge_is_NA_if_speed_is_undefined(self):
        self.a1.speed = None
        self.b1.speed = None

        results = Edge((self.a, self.b), (self.a1, self.b1)).to_json()

        self.assertEqual(results['link_speed'], 'N/A')

    def test_stubbed_netbox_always_gives_is_elink(self):
        netbox = stubs.Netbox()
        netbox.sysname = 'IamStub'
        netbox.id = netbox.sysname
        netbox.category_id = 'ELINK'
        self.assertEqual(
            {
                'category': 'ELINK',
                'id': 'IamStub',
                'is_elink_node': True,
                'position': {'x': 1.3, 'y': 3.7},
                'sysname': 'IamStub',
            },
            metadata.Node(netbox, self.nx_edge_metadata).to_json()['IamStub'],
        )

    def test_json_id_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('id' in foo)
        self.assertEqual('2', foo['id'])

    def test_json_sysname_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('sysname' in foo)
        self.assertEqual('a', foo['sysname'])

    def test_json_category_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('category' in foo)
        self.assertEqual('GW', foo['category'])

    def test_json_ip_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('ip' in foo)
        self.assertEqual('::2', foo['ip'])

    def test_json_ipdevinfo_link_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('ipdevinfo_link' in foo)
        self.assertEqual('/ipdevinfo/a/', foo['ipdevinfo_link'])

    def test_json_position_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('position' in foo)
        self.assertEqual({'x': 1.3, 'y': 3.7}, foo['position'])

    def test_json_position_is_not_in_json_if_position_data_not_available_from_graph(
        self,
    ):
        del self.nx_edge_metadata['metadata']['position']
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertFalse('position' in foo)

    def test_json_up_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('up' in foo)
        self.assertEqual('y', foo['up'])

    def test_json_up_image_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('up_image' in foo)
        self.assertEqual('green.png', foo['up_image'])

    def test_json_roomid_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('roomid' in foo)
        self.assertEqual('Pegasus', foo['roomid'])

    def test_json_locationid_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('locationid' in foo)
        self.assertEqual('galaxy', foo['locationid'])

    def test_json_location_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('location' in foo)
        self.assertEqual('In a galaxy far far away', foo['location'])

    def test_json_room_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('room' in foo)
        self.assertEqual('Pegasus (room description)', foo['room'])

    def test_json_is_elink_node_is_included_in_metadata_from_node(self):
        foo = metadata.Node(self.a, self.nx_edge_metadata).to_json()['2']
        self.assertTrue('is_elink_node' in foo)
        self.assertFalse(foo['is_elink_node'])


class Layer2JsonMetadataTests(SharedJsonMetadataTests, TopologyLayer2TestCase):
    def setUp(self):
        super(Layer2JsonMetadataTests, self).setUp()

        a_position = NetmapViewNodePosition()
        a_position.x = 1.3
        a_position.y = 3.7
        self.nx_edge_metadata = {'metadata': {'position': a_position}}
        self.nx_node_metadata = {
            'metadata': {
                'vlans': [
                    (
                        1337,
                        SwPortVlan(
                            id=1231,
                            interface=self.a1,
                            vlan=Vlan(id=1337, vlan=10, net_ident='unittest vlan'),
                        ),
                    )
                ]
            }
        }

    def test_json_node_contains_vlan_data(self):
        foo = metadata.node_to_json_layer2(self.a, self.nx_node_metadata)['2']
        self.assertTrue('vlans' in foo)
        self.assertEqual(1, len(foo['vlans']))

        # nav_vlan_id (key) should equal swpv.vlan.id
        self.assertEqual(
            self.nx_node_metadata.get('metadata')['vlans'][0][0],
            self.nx_node_metadata.get('metadata')['vlans'][0][1].vlan.id,
        )

        # nav_vlan_id == swpv.vlan.id
        self.assertEqual(1337, foo['vlans'][0])  # vlan.nav_vlan


class Layer3JsonMetadataTests(SharedJsonMetadataTests, TopologyLayer3TestCase):
    def setUp(self):
        super(Layer3JsonMetadataTests, self).setUp()

        a_position = NetmapViewNodePosition()
        a_position.x = 1.3
        a_position.y = 3.7
        self.nx_edge_metadata = {'metadata': {'position': a_position}}

    def test_layer3_prefix_is_added_between_a_and_b(self):
        nx_meta = self.netmap_graph.get_edge_data(self.a, self.b)
        edge_json_metadata = metadata.edge_to_json_layer3((self.a, self.b), nx_meta)

        self.assertEqual(1, len(edge_json_metadata['edges']))
        self.assertEqual(
            '158.38.0.0/30',
            edge_json_metadata['edges'][2111][0]['prefix']['net_address'],
        )

    def test_layer3_v4_and_v6_prefixes_added_between_a_and_c(self):
        edge_json_metadata = metadata.edge_to_json_layer3(
            (self.a, self.b), self.netmap_graph.get_edge_data(self.a, self.c)
        )

        self.assertEqual(1, len(edge_json_metadata['edges']))
        self.assertEqual(2, len(edge_json_metadata['edges'][2112]))
        expected_prefixes = ('158.38.0.4/30', 'feed:dead:cafe:babe::/64')
        for i, prefix in enumerate(expected_prefixes):
            self.assertEqual(
                edge_json_metadata['edges'][2112][i]['prefix']['net_address'], prefix
            )


if __name__ == '__main__':
    unittest.main()

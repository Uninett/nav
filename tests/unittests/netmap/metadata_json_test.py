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
from nav.models.manage import (Netbox, Room, Location, SwPortVlan, Vlan,
    Interface)
from nav.models.profiles import NetmapViewNodePosition
from nav.netmap import stubs, metadata
from nav.netmap.metadata import edge_to_json, edge_to_json_layer3, Edge, Group
from metaclass_testcase import MetaClassTestCase
from topology_layer3_testcase import TopologyLayer3TestCase
from topology_layer2_testcase import TopologyLayer2TestCase


class MetaClassesJsonTests(MetaClassTestCase):

    def setUp(self):
        super(MetaClassesJsonTests, self).setUp()

    def test_allow_group_interface_to_be_none(self):
        json = Group(self.netbox).to_json()
        self.assertFalse('interface' in json)
        self.assertEquals(
            {'netbox': {'category': 'GW',
                        'id': '1337',
                        'ip': '192.168.42.1',
                        'ipdevinfo_link': '/ipdevinfo/fuu.example.net/',
                        'is_elink_node': False,
                        'location': u'Far far away',
                        'locationid': u'Universe',
                        'position': None,
                        'room': "Galaxy (Universe Far Far away)",
                        'roomid': 'Galaxy',
                        'sysname': 'fuu.example.net',
                        'up': 'y',
                        'up_image': 'green.png'}
            }
            , json)

    def test_group_renders_gw_ip_if_included(self):
        assert self.netbox is not None
        group = Group(self.netbox)
        group.gw_ip = '192.168.42.254'
        json = group.to_json()
        self.assertTrue('gw_ip' in json)
        self.assertEquals('192.168.42.254', json['gw_ip'])

    def test_group_renders_virtual_if_included_and_value_is_true(self):
        group = Group(self.netbox)
        group.virtual = True
        json = group.to_json()
        self.assertTrue('virtual' in json)
        self.assertEquals(True, json['virtual'])

    def test_group_renders_virtual_if_included_and_value_is_false(self):
        group = Group(self.netbox)
        group.virtual = False
        json = group.to_json()
        self.assertTrue('virtual' in json)
        self.assertEquals(False, json['virtual'])


class SharedJsonMetadataTests():
    def test_not_failing_when_both_interface_speed_is_undefined(self):
        self.a1.speed = None
        self.b1.speed = None
        results = Edge(self.a1, self.b1)
        self.assertTrue(results.link_speed is None)

    def test_json_edge_is_NA_if_speed_is_undefined(self):
        self.a1.speed = None
        self.b1.speed = None

        results = edge_to_json(None, Edge(self.a1, self.b1))

        self.assertEquals(results['link_speed'], 'N/A')

    def test_stubbed_netbox_always_gives_is_elink(self):
        netbox = stubs.Netbox()
        netbox.sysname = 'IamStub'
        netbox.category_id = 'ELINK'
        self.assertEqual({
                             'category': 'ELINK',
                             'is_elink_node': True,
                             'sysname': 'IamStub'
                         },
                         metadata._node_to_json(netbox, self.nx_edge_metadata))

    def test_json_id_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('id' in foo)
        self.assertEqual('2', foo['id'])

    def test_json_sysname_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('sysname' in foo)
        self.assertEqual('a', foo['sysname'])

    def test_json_category_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('category' in foo)
        self.assertEqual('GW', foo['category'])

    def test_json_ip_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('ip' in foo)
        self.assertEqual('::2', foo['ip'])

    def test_json_ipdevinfo_link_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('ipdevinfo_link' in foo)
        self.assertEqual('/ipdevinfo/a/', foo['ipdevinfo_link'])

    def test_json_position_is_included_in_metadata_from_node(self):
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('position' in foo)
        self.assertEqual({'x': 1.3, 'y': 3.7}, foo['position'])

    def test_json_position_is_none_if_not_available_in_metadata_from_node(self):
        del self.nx_edge_metadata['metadata']['position']
        foo = metadata._node_to_json(self.a, self.nx_edge_metadata)
        self.assertTrue('position' in foo)
        self.assertEqual(None, foo['position'])

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


class Layer2JsonMetadataTests(SharedJsonMetadataTests, TopologyLayer2TestCase):
    def setUp(self):
        super(Layer2JsonMetadataTests, self).setUp()

        a_position = NetmapViewNodePosition()
        a_position.x = 1.3
        a_position.y = 3.7
        self.nx_edge_metadata = {'metadata': {
            'position': a_position
        }}
        self.nx_node_metadata = {'metadata': {
            'vlans': [(1337, SwPortVlan(id=1231, interface=self.a1,
                                        vlan=Vlan(id=1337, vlan=10,
                                                  net_ident='unittest vlan')))]
        }}

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


class Layer3JsonMetadataTests(SharedJsonMetadataTests, TopologyLayer3TestCase):
    def setUp(self):
        super(Layer3JsonMetadataTests, self).setUp()

        a_position = NetmapViewNodePosition()
        a_position.x = 1.3
        a_position.y = 3.7
        self.nx_edge_metadata = {'metadata': {
            'position': a_position
        }}

    def test_layer3_prefix_is_added_between_a_and_b(self):
        self._setupNetmapGraphLayer3()
        edge_json_metadata = edge_to_json_layer3(
            (self.a, self.b),
            self.netmap_graph.get_edge_data(self.a, self.b)
        )

        self.assertEqual(1, len(edge_json_metadata))
        self.assertEqual(1, len(
            edge_json_metadata[0].get('prefixes')))
        self.assertEqual(u'158.38.0.0/30 (vlan 50)',
                         edge_json_metadata[0].get('prefixes')[0])

    def test_layer3_v4_and_v6_prefixes_added_between_a_and_c(self):
        self._setupNetmapGraphLayer3()
        edge_json_metadata = edge_to_json_layer3(
            (self.a, self.b),
            self.netmap_graph.get_edge_data(self.a, self.c)
        )

        self.assertEqual(1, len(edge_json_metadata))
        self.assertEqual(2, len(
            edge_json_metadata[0].get('prefixes')))
        expected_prefixes = (u'158.38.0.4/30 (vlan 50)', u'feed:dead:cafe:babe::/64 (vlan 50)')
        test = edge_json_metadata[0].get('prefixes')

        self.assertTrue(
            all([x in test for x in expected_prefixes])
            , msg="Didn't find all keys {0}, only found: {1}".format(
                expected_prefixes,
                test
            )
        )


if __name__ == '__main__':
    unittest.main()
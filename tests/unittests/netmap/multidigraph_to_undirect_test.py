import unittest
import mock
import networkx as nx
from nav.models.manage import SwPortVlan, Vlan
from nav.netmap import topology
from nav.netmap.metadata import edge_to_json_layer2, edge_metadata_layer2
from nav.netmap.topology import \
    _convert_to_unidirectional_and_attach_directional_metadata
from nav.topology import vlan
from topology_testcase import TopologyTestCase


class MultiGraphToUndirectTests(TopologyTestCase):

    def test_b1_and_b2_netbox_is_the_same(self):
        self.assertEqual(self.b1.netbox, self.b2.netbox, msg="Critical, interfaces connected to same netbox must be of the same netbox instance")

    # This is basically what a standard NAV topology graph looks like...
    # we need to make it unidirectional while keeping attr_dict
    # from all edges

    # [1 / 2]
    def test_nodes_length_of_orignal_graph_consists_with_nav_topology_behavior(self):
        self.assertEquals(4, len(self.nav_graph.nodes()), msg="Original NAV graph should only contain 2 nodes, it contains: "+unicode(self.nav_graph.nodes()))

    # [2 / 2]
    def test_edges_length_of_orginal_graph_consists_with_nav_topology_behavior(self):
        self.assertEquals(6, len(self.nav_graph.edges()))



    # netmap graphs tests below

    def test_nodes_length_of_netmap_graph_is_reduced_properly(self):
        self._setupNetmapGraph()
        # four nodes, A, B, C and D
        self.assertEquals(4, len(self.netmap_graph.nodes()))

    def test_edges_length_of_netmap_graph_is_reduced_properly(self):
        self._setupNetmapGraph()
        # one LINE between A and B.
        # one LINE between B and C
        # one line between C and D
        self.assertEqual(3, len(self.netmap_graph.edges()))
        self.assertEqual(
            [
                (self.a, self.b),
                (self.a, self.c),
                (self.c, self.d)
            ],
            self.netmap_graph.edges()
        )

    def test_layer2_create_directional_metadata_from_nav_graph(self):
        #foo = self.nav_graph.get_edge_data(self.a, self.b, key=self.a1)
        self._setupTopologyVlanMock()
        self.netmap_graph = _convert_to_unidirectional_and_attach_directional_metadata(
            self.nav_graph,
            edge_metadata_layer2,
            topology._get_vlans_map_layer2()[0]
        )

        # should be the same as
        #  test_edges_length_of_netmap_graph_is_reduced_properly
        self.assertEqual(
            [
                (self.a, self.b),
                (self.a, self.c),
                (self.c, self.d)
            ],
            self.netmap_graph.edges()
        )

    def test_netmap_metadata_shows_2_links_for_edge_between_a_and_b(self):
        self._setupNetmapGraph()

        self.assertEquals(2, len(self.netmap_graph.get_edge_data(
            self.a,
            self.b
        ).get('meta', [])))

    def test_netmap_metadata_is_correct_for_2_links_edge_between_a_and_b(self):
        self._setupNetmapGraph()
        self.maxDiff = None
        self.assertEquals(
            [
                {
                    'tip_inspect_link': False,
                    'link_speed': None,
                    'uplink': {
                            'thiss': {
                                'interface': self.a1,
                                'netbox': self.a
                            },
                            'other': {
                                'interface': self.b1,
                                'netbox': self.b
                            },
                            'vlans': [self.vlan__a1_b1],
                        },

                    'error': {}
                 },
                {
                    'tip_inspect_link': False,
                    'link_speed': None,
                    'uplink': {
                            'thiss': {
                                'interface': self.a2,
                                'netbox': self.a
                            },
                            'other': {
                                'interface': self.b2,
                                'netbox': self.b
                            },
                            'vlans': [],
                        },
                    'error': {}
                 },
            ],
            self.netmap_graph.get_edge_data(self.a, self.b).get('meta', {}))

if __name__ == '__main__':
    unittest.main()
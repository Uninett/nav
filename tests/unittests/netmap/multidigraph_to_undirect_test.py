import unittest
from nav.netmap import topology
from nav.netmap.metadata import edge_metadata_layer2
from nav.netmap.topology import \
    _convert_to_unidirectional_and_attach_directional_metadata

from topology_layer2_testcase import TopologyLayer2TestCase
from topology_layer3_testcase import TopologyLayer3TestCase


class Layer2MultiGraphToUndirectTests(TopologyLayer2TestCase):

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
        self._setupNetmapGraphLayer2()
        # four nodes, A, B, C and D
        self.assertEquals(4, len(self.netmap_graph.nodes()))

    def test_edges_length_of_netmap_graph_is_reduced_properly(self):
        self._setupNetmapGraphLayer2()
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
        self._setupTopologyLayer2VlanMock()
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

        self.assertEqual(2,
                         len(self.netmap_graph.get_edge_data(
                             self.a,
                             self.b
                         ).get('meta', [])))

class Layer3MultiGraphToUndirectTests(TopologyLayer3TestCase):

    def test_nodes_length_of_orignal_graph_consists_with_nav_topology_behavior(self):
        # 9 gwport prefixes.
        self.assertEqual(9, len(self.nav_graph.nodes()))

    def test_edges_length_of_original_graph_consiits_with_nav_topology_behavior(self):
        # 6 edges between gw port prefixes keyed on prefix.
        self.assertEqual(6, len(self.nav_graph.edges()))

if __name__ == '__main__':
    unittest.main()
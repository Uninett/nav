import unittest

from nav.netmap import topology
from nav.netmap.topology import build_netmap_layer2_graph

from .topology_layer2_testcase import TopologyLayer2TestCase
from .topology_layer3_testcase import TopologyLayer3TestCase


class Layer2MultiGraphToUndirectTests(TopologyLayer2TestCase):
    def test_b1_and_b2_netbox_is_the_same(self):
        self.assertEqual(
            self.b1.netbox,
            self.b2.netbox,
            msg="Critical, interfaces connected to same netbox must be of the same"
            "netbox instance",
        )

    # This is basically what a standard NAV topology graph looks like...
    # we need to make it unidirectional while keeping attr_dict
    # from all edges

    # [1 / 2]
    def test_nodes_length_of_orignal_graph_consists_with_nav_topology_behavior(self):
        self.assertEqual(
            4,
            len(self.nav_graph.nodes()),
            msg="Original NAV graph should only contain 2 nodes, it contains: "
            + str(self.nav_graph.nodes()),
        )

    # [2 / 2]
    def test_edges_length_of_orginal_graph_consists_with_nav_topology_behavior(self):
        self.assertEqual(6, len(self.nav_graph.edges()))

    # netmap graphs tests below

    def test_nodes_length_of_netmap_graph_is_reduced_properly(self):
        # four nodes, A, B, C and D
        self.assertEqual(4, len(self.netmap_graph.nodes()))

    def test_edges_length_of_netmap_graph_is_reduced_properly(self):
        # one LINE between A and B.
        # one LINE between A and C
        # one line between C and D
        self.assertEqual(3, len(self.netmap_graph.edges()))
        self.assertIn((self.a, self.b), self.netmap_graph.edges())
        self.assertIn((self.a, self.c), self.netmap_graph.edges())
        self.assertIn((self.c, self.d), self.netmap_graph.edges())

    def test_layer2_create_directional_metadata_from_nav_graph(self):
        self.netmap_graph = build_netmap_layer2_graph(
            self.nav_graph,
            topology._get_vlans_map_layer2(self.nav_graph)[0],
            topology._get_vlans_map_layer2(self.nav_graph)[1],
        )

        # should be the same as
        #  test_edges_length_of_netmap_graph_is_reduced_properly
        self.assertIn((self.a, self.b), self.netmap_graph.edges())
        self.assertIn((self.a, self.c), self.netmap_graph.edges())
        self.assertIn((self.c, self.d), self.netmap_graph.edges())

        self.assertEqual(
            2, len(self.netmap_graph.get_edge_data(self.a, self.b).get('metadata', []))
        )


class Layer3MultiGraphToUndirectTests(TopologyLayer3TestCase):
    def test_nodes_length_of_orignal_graph_consists_with_nav_topology_behavior(self):
        # 11 gwport prefixes.
        self.assertEqual(11, len(self.nav_graph.nodes()))

    def test_edges_length_of_original_graph_consiits_with_nav_topology_behavior(self):
        # 7 edges between gw port prefixes keyed on gw port prefix.
        self.assertEqual(7, len(self.nav_graph.edges()))

    def test_nodes_length_of_netmap_graph_is_reduced_properly(self):
        print(self.netmap_graph.nodes())
        self.assertEqual(7, len(self.netmap_graph.nodes()))

    def test_edges_length_of_netmap_graph_is_reduced_properly(self):
        self.assertEqual(6, len(self.netmap_graph.edges()))

    def test_layer3_edges_is_as_expected_in_netmap_graph(self):
        for edge in [
            (self.a, self.b),
            (self.a, self.c),
            (self.b, self.d),
            (self.b, self.e),
            (self.d, self.e),
            (self.f, self.unknown),
        ]:
            self.assertTrue(self.netmap_graph.has_edge(*edge))

    def test_layer3_only_one_vlan_on_all_edges(self):
        """ """
        self.assertEqual(
            1,
            len(self.netmap_graph.get_edge_data(self.a, self.b).get('metadata').keys()),
        )
        self.assertEqual(
            1,
            len(self.netmap_graph.get_edge_data(self.a, self.c).get('metadata').keys()),
        )
        self.assertEqual(
            1,
            len(self.netmap_graph.get_edge_data(self.b, self.d).get('metadata').keys()),
        )
        self.assertEqual(
            1,
            len(self.netmap_graph.get_edge_data(self.b, self.e).get('metadata').keys()),
        )
        self.assertEqual(
            1,
            len(self.netmap_graph.get_edge_data(self.d, self.e).get('metadata').keys()),
        )
        self.assertEqual(
            1,
            len(
                self.netmap_graph.get_edge_data(self.f, self.unknown)
                .get('metadata')
                .keys()
            ),
        )

    def test_layer3__a__c__vlan_contains_both_v4_and_v6_prefixes(self):
        self.assertEqual(
            2,
            len(
                self.netmap_graph.get_edge_data(self.a, self.c)
                .get('metadata')
                .get(2112)
            ),
        )


if __name__ == '__main__':
    unittest.main()

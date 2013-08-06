import pytest
from nav.models.manage import Interface
from nav.netmap.metadata import Edge, Group
from topology_layer2_testcase import TopologyLayer2TestCase
from topology_layer3_testcase import TopologyLayer3TestCase


class SharedNetworkXMetadataTests(object):
    def test_this_shared_networkx_metadata_test_is_running(self):
        self.assertTrue(True) # Nice to check on CI if it has been run.

    def test_metadata_is_of_type_array(self):
        for node_a, node_b in self.netmap_graph.edges():
            metadata = self._get_metadata(node_a, node_b)

            assert type(metadata) == list


class Layer2NetworkXMetadataTests(SharedNetworkXMetadataTests, TopologyLayer2TestCase):
    def setUp(self):
        super(Layer2NetworkXMetadataTests, self).setUp()
        self._setupNetmapGraphLayer2()

    def _get_metadata(self, node_a, node_b, metadata_key='metadata'):
        return self.netmap_graph.get_edge_data(node_a, node_b).get(metadata_key)

    def test_metadata_contains_edge_objects(self):
        for node_a, node_b in self.netmap_graph.edges():
            metadata = self._get_metadata(node_a, node_b)

            for pair in metadata:
                assert type(pair) == Edge
                assert type(pair) == Edge



    def test_node_a1_and_b1_contains_vlan_metadata(self):
        vlans = self.netmap_graph.node[self.a]['metadata']['vlans']

        self.assertEqual(1, len(vlans))
        self.assertEqual(vlans[0][1], self.vlan__a1_b1)
        # nav_vlan_id == SwPortVlan.Vlan.Id
        self.assertEqual(vlans[0][0], self.vlan__a1_b1.vlan.id)

    def test_edge_between_a_and_b_has_2_edges_as_metdata(self):
        edge_meta = self._get_metadata(self.a, self.b)
        self.assertEqual(2, len(edge_meta))

    def test_edge_between_a_and_b_contains_a1_b1__and__a2_b2_uplinks(self):
        pairs = list(self._get_metadata(self.a, self.b))

        self.assertEqual(self.a1, pairs[0].source.interface)
        self.assertEqual(self.b1, pairs[0].target.interface)
        self.assertEqual(self.a2, pairs[1].source.interface)
        self.assertEqual(self.b2, pairs[1].target.interface)


    def test_netmap_metadata_shows_2_links_for_edge_between_a_and_b(self):
        self._setupNetmapGraphLayer2()
        self.assertEquals(2, len(self._get_metadata(self.a, self.b)))

    def test_netmap_metadata_is_correct_for_2_links_edge_between_a_and_b(self):
        self._setupNetmapGraphLayer2()
        self.maxDiff = None
        assert [
                   Edge(source=self.a1,
                        target=self.b1,
                        vlans=[self.vlan__a1_b1]),
                   Edge(source=self.a2,
                        target=self.b2)
               ] == (self.netmap_graph.get_edge_data(self.a, self.b) or {}).get(
            'metadata')


class Layer3NetworkXMetadataTests(SharedNetworkXMetadataTests, TopologyLayer3TestCase):
    def setUp(self):
        super(Layer3NetworkXMetadataTests, self).setUp()
        self._setupNetmapGraphLayer3()

    def _get_metadata(self, node_a, node_b):
        return [x.get('metadata') for x in self.netmap_graph.get_edge_data(node_a, node_b).values()]

    def test_link_between_a_and_c_contains_both_v4_and_v6_prefix(self):
        self.assertEqual(
            [self.prefix_bar, self.prefix_bar_ipv6],

            self.netmap_graph.get_edge_data(
                self.a, self.c
            ).get(2112)
            .get('metadata').prefixes
        )

    def test_link_got_prefixed_attached(self):
        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.a, self.b
        ).get(self.prefix_foo.vlan.id)
        .get('metadata').prefixes))

        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.b, self.d
        ).get(self.prefix_baz.vlan.id)
        .get('metadata').prefixes))

        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.b, self.e
        ).get(self.prefix_baz.vlan.id)
        .get('metadata').prefixes))

        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.f, self.unknown
        ).get(self.prefix_zar.vlan.id)
        .get('metadata').prefixes))

    def test_edge_source_has_correct_metadata(self):
        # 2111 is VLAN.id
        source = self.netmap_graph.get_edge_data(self.a, self.b).get(2111).get(
            'metadata').source
        self.assertEqual(source.interface, self.b1)
        self.assertEqual(source.netbox, self.b)
        self.assertEqual(source.gw_ip, '158.38.0.2')
        self.assertFalse(source.virtual)

    def test_edge_target_has_correct_metadata(self):
        target = self.netmap_graph.get_edge_data(self.a, self.b).get(2111).get(
            'metadata').target
        self.assertEqual(target.interface, self.a1)
        self.assertEqual(target.netbox, self.a)
        self.assertEqual(target.gw_ip, '158.38.0.1')
        self.assertFalse(target.virtual)

    def test_uplink_has_all_layer3_properties_it_should_for_source(self):
        should_have = ('gw_ip', 'virtual')

        metadata = self.netmap_graph.get_edge_data(self.a, self.b).get(
            2111).get('metadata')

        self.assertTrue(
            all([hasattr(metadata.target, attribute) for attribute in should_have]),
            msg="Didn't find all keys {0}, only found: {1}".format(
                should_have,
                metadata.__dict__.keys()
            )
        )

    def test_uplink_has_all_layer3_properties_it_should_for_target(self):
        should_have = ('gw_ip', 'virtual')

        metadata = self.netmap_graph.get_edge_data(self.a, self.b).get(
            2111).get('metadata')

        self.assertTrue(
            all([hasattr(metadata.target, attribute) for attribute in should_have]),
            msg="Didn't find all keys {0}, only found: {1}".format(
                should_have,
                metadata.__dict__.keys()
            )
        )

    def test_uplink_has_all_layer3_properties_it_should(self):
        should_have = ('prefixes', 'vlan')
        for metadata in self.netmap_graph.get_edge_data(self.a, self.b).values():
            self.assertTrue(
                all(
                    [hasattr(metadata.get('metadata'), y) for y in should_have]
                ),
                msg="Didn't find all keys {0}, only found: {1}".format(
                should_have,
                metadata.get('metadata').__dict__.keys()
            ))
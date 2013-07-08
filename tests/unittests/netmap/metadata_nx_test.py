from topology_layer2_testcase import TopologyLayer2TestCase
from topology_layer3_testcase import TopologyLayer3TestCase


class Layer2NetworkXMetadataTests(TopologyLayer2TestCase):
    def setUp(self):
        super(Layer2NetworkXMetadataTests, self).setUp()
        self._setupNetmapGraphLayer2()

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

    def test_fetch_link_speed_from_edge(self):
        a, b, meta = self.netmap_graph.edges(data=True)[0]
        self.assertTrue('link_speed' in meta['meta'][0])

    def test_netmap_metadata_shows_2_links_for_edge_between_a_and_b(self):
        self._setupNetmapGraphLayer2()
        self.assertEquals(2, len(self.netmap_graph.get_edge_data(
            self.a,
            self.b
        ).get('meta', [])))

    def test_netmap_metadata_is_correct_for_2_links_edge_between_a_and_b(self):
        self._setupNetmapGraphLayer2()
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


class Layer3NetworkXMetadataTests(TopologyLayer3TestCase):
    def setUp(self):
        super(Layer3NetworkXMetadataTests, self).setUp()
        self._setupNetmapGraphLayer3()

    def test_link_between_a_and_c_contains_both_v4_and_v6_prefix(self):
        self.assertEqual(
            [self.prefix_bar, self.prefix_bar_ipv6],

            self.netmap_graph.get_edge_data(
                self.a, self.c
            ).get(2112)
            .get('metadata')
            .get('uplink')
            .get('prefixes')
        )

    def test_link_got_prefixed_attached(self):
        self._setupNetmapGraphLayer3()
        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.a, self.b
        ).get(self.prefix_foo.vlan.id)
        .get('metadata')
        .get('uplink')
        .get('prefixes')))

        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.b, self.d
        ).get(self.prefix_baz.vlan.id)
        .get('metadata')
        .get('uplink')
        .get('prefixes')))

        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.b, self.e
        ).get(self.prefix_baz.vlan.id)
        .get('metadata')
        .get('uplink')
        .get('prefixes')))

        self.assertEqual(1, len(self.netmap_graph.get_edge_data(
            self.f, self.unknown
        ).get(self.prefix_zar.vlan.id)
        .get('metadata')
        .get('uplink')
        .get('prefixes')))


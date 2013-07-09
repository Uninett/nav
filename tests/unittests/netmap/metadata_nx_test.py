from topology_layer2_testcase import TopologyLayer2TestCase
from topology_layer3_testcase import TopologyLayer3TestCase


class SharedNetworkXMetadataTests(object):
    def test_this_shared_networkx_metadata_test_is_running(self):
        self.assertTrue(True) # Nice to check on CI if it has been run.

    def test_root_metadata_has_all_properties_it_should(self):
        for node_a, node_b in self.netmap_graph.edges():
            metadata = self._get_metadata(node_a, node_b)
            for x in metadata:
                self.assertTrue(all([x in ('tip_inspect_link', 'link_speed', 'uplink', 'error') for x in x.keys()]))

    def test_uplink_has_all_shared_properties_it_should_for_uplink__this(self):
        # for every uplink. (MultiDiGraph Directed Metadata)
        for node_a, node_b in self.netmap_graph.edges():
            collection_metadata = self._get_metadata(node_a, node_b)

            should_have = ('netbox', 'interface')

            for metadata in collection_metadata:
                keys_uplink_side = metadata.get('uplink').get('thiss').keys()
                self.assertTrue(all([x in keys_uplink_side for x in should_have])
                    , msg="Didn't find all keys {0}, only found: {1}".format(
                        should_have,
                        keys_uplink_side
                    ))

    def test_uplink_has_all_shared_properties_it_should_for_uplink__other(self):
        # for every uplink. (MultiDiGraph Directed Metadata)
        for node_a, node_b in self.netmap_graph.edges():
            collection_metadata = self._get_metadata(node_a, node_b)

            should_have = ('netbox', 'interface')

            for metadata in collection_metadata:
                keys_uplink_side = metadata.get('uplink').get('other').keys()

                self.assertTrue(all([x in keys_uplink_side for x in should_have])
                    , msg="Didn't find all keys {0}, only found: {1}".format(
                        should_have,
                        keys_uplink_side
                    ))

    def test_uplink_has_all_shared_properties_it_should(self):
        for node_a, node_b in self.netmap_graph.edges():
            metadata = self._get_metadata(node_a, node_b)
            should_have = ('thiss', 'other')
            for x in metadata:
                uplink_keys = x.get('uplink').keys()
                self.assertTrue(
                    all([y in uplink_keys for y in should_have]),
                    msg="Didn't find all keys {0}, only found: {1}"
                    .format(
                        should_have,
                        uplink_keys
                    )
                )


class Layer2NetworkXMetadataTests(SharedNetworkXMetadataTests, TopologyLayer2TestCase):
    def setUp(self):
        super(Layer2NetworkXMetadataTests, self).setUp()
        self._setupNetmapGraphLayer2()

    def _get_metadata(self, node_a, node_b):
        return self.netmap_graph.get_edge_data(node_a, node_b).get('metadata')

    def test_node_a1_and_b1_contains_vlan_metadata(self):
        vlans = self.netmap_graph.node[self.a]['metadata']['vlans']

        self.assertEqual(1, len(vlans))
        self.assertEqual(vlans[0][1], self.vlan__a1_b1)
        # nav_vlan_id == SwPortVlan.Vlan.Id
        self.assertEqual(vlans[0][0], self.vlan__a1_b1.vlan.id)

    def test_edge_between_a_and_b_has_2_edges_as_metdata(self):
        edge_meta = self.netmap_graph.get_edge_data(self.a, self.b)['metadata']
        self.assertEqual(2, len(edge_meta))

    def test_edge_between_a_and_b_contains_a1_b1__and__a2_b2_uplinks(self):
        edge_meta = [x['uplink'] for x in
                     self.netmap_graph.get_edge_data(self.a, self.b)['metadata']]
        self.assertEqual(self.a1, edge_meta[0]['thiss']['interface'])
        self.assertEqual(self.b1, edge_meta[0]['other']['interface'])
        self.assertEqual(self.a2, edge_meta[1]['thiss']['interface'])
        self.assertEqual(self.b2, edge_meta[1]['other']['interface'])


    def test_netmap_metadata_shows_2_links_for_edge_between_a_and_b(self):
        self._setupNetmapGraphLayer2()
        self.assertEquals(2, len(self.netmap_graph.get_edge_data(
            self.a,
            self.b
        ).get('metadata', [])))

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
            self.netmap_graph.get_edge_data(self.a, self.b).get('metadata', {}))


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
            .get('metadata')
            .get('uplink')
            .get('prefixes')
        )

    def test_link_got_prefixed_attached(self):
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

    def test_uplink_has_thiss_has_correct_metadata(self):
        # 2111 is VLAN.id
        thiss = self.netmap_graph.get_edge_data(self.a, self.b).get(2111).get(
            'metadata').get('uplink').get('thiss')
        self.assertEqual(thiss['interface'], self.b1)
        self.assertEqual(thiss['netbox'], self.b)
        self.assertEqual(thiss['gw_ip'], '158.38.0.2')
        self.assertFalse(thiss['virtual'])

    def test_uplink_has_other_has_correct_metadata(self):
        other = self.netmap_graph.get_edge_data(self.a, self.b).get(2111).get(
            'metadata').get('uplink').get('other')
        self.assertEqual(other['interface'], self.a1)
        self.assertEqual(other['netbox'], self.a)
        self.assertEqual(other['gw_ip'], '158.38.0.1')
        self.assertFalse(other['virtual'])

    def test_uplink_has_all_layer3_properties_it_should_for_uplink__this(self):
        should_have = ('gw_ip', 'virtual')

        metadata = self.netmap_graph.get_edge_data(self.a, self.b).get(
            2111).get('metadata').get('uplink').get('thiss').keys()

        self.assertTrue(
            all([x in metadata for x in should_have])
            , msg="Didn't find all keys {0}, only found: {1}".format(
                should_have,
                metadata
            )
        )

    def test_uplink_has_all_layer3_properties_it_should_for_uplink__other(self):
        should_have = ('gw_ip', 'virtual')

        metadata = self.netmap_graph.get_edge_data(self.a, self.b).get(
            2111).get('metadata').get('uplink').get('other').keys()

        self.assertTrue(
            all([x in metadata for x in should_have]),
            msg="Didn't find all keys {0}, only found: {1}".format(
                should_have,
                metadata
            )
        )

    def test_uplink_has_all_layer3_properties_it_should(self):
        should_have = ('prefixes', 'vlan')
        for x in self.netmap_graph.get_edge_data(self.a, self.b).values():
            self.assertTrue(
                all(
                    [y in x.get('metadata').get('uplink').keys() for y in should_have]
                ),
                msg="Didn't find all keys {0}, only found: {1}".format(
                should_have,
                x.get('metadata').get('uplink').keys()
            ))
from mock import Mock
import pytest
import unittest
from nav.models.manage import Interface, Netbox
from nav.netmap.metadata import Edge, Group
from topology_layer2_testcase import TopologyLayer2TestCase
from topology_layer3_testcase import TopologyLayer3TestCase
from metaclass_testcase import MetaClassTestCase

class MetaClassesTests(MetaClassTestCase):
    def setUp(self):
        super(MetaClassTestCase, self).setUp()

    def test_group_does_not_raise_exception_when_interface_is_none(self):
        foo  = Group(Mock(name='netbox', spec=Netbox), None)

    def test_edge_allows_both_interface_linkspeed_in_group_to_be_none(self):
        netbox_a = Mock(name='netbox a', sepc=Netbox)
        netbox_a.id = 'foo'
        a = Mock(name='interface a', spec=Interface)
        a.speed = None

        netbox_b = Mock(name='netbox b', spec=Netbox)
        netbox_b.id = 'bar'
        b = Mock(name='interface b', spec=Interface)
        b.speed = None

        foo = Edge((netbox_a, netbox_b), a, b)



class Layer2NetworkXMetadataTests(TopologyLayer2TestCase):
    def setUp(self):
        super(Layer2NetworkXMetadataTests, self).setUp()

    def _get_metadata(self, node_a, node_b, metadata_key='metadata'):
        return self.netmap_graph.get_edge_data(node_a, node_b).get(metadata_key)

    def test_metadata_contains_edge_objects(self):
        for node_a, node_b, metadata in self.netmap_graph.edges(data=True):
            for pair in metadata.get('metadata'):
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
        self.assertEquals(2, len(self._get_metadata(self.a, self.b)))

    def test_netmap_metadata_is_correct_for_2_links_edge_between_a_and_b(self):
        self.maxDiff = None
        assert [
                   Edge(nx_edge=(self.a, self.b),
                        source=self.a1,
                        target=self.b1,
                        ),
                   Edge(nx_edge=(self.a, self.b),
                        source=self.a2,
                        target=self.b2)
               ] == (self.netmap_graph.get_edge_data(self.a, self.b) or {}).get(
            'metadata')


class Layer3NetworkXMetadataTests(TopologyLayer3TestCase):
    def setUp(self):
        super(Layer3NetworkXMetadataTests, self).setUp()

    def test_link_between_a_and_c_contains_both_v4_and_v6_prefix(self):
        self.assertEqual(
            [self.prefix_bar_ipv6, self.prefix_bar],

            [edge.prefix for edge in self.netmap_graph.get_edge_data(
                self.a, self.c
            ).get('metadata').get(2112)]
        )

    def test_link_got_prefixed_attached(self):
        self.assertEqual(self.prefix_foo, self.netmap_graph.get_edge_data(
            self.a, self.b
        ).get('metadata').get(self.prefix_foo.vlan.id)[0].prefix)

        self.assertEqual(self.prefix_baz, self.netmap_graph.get_edge_data(
            self.b, self.d
        ).get('metadata').get(self.prefix_baz.vlan.id)[0].prefix)

        self.assertEqual(self.prefix_baz, self.netmap_graph.get_edge_data(
            self.b, self.e
        ).get('metadata').get(self.prefix_baz.vlan.id)[0].prefix)

        self.assertEqual(self.prefix_zar, self.netmap_graph.get_edge_data(
            self.f, self.unknown
        ).get('metadata').get(self.prefix_zar.vlan.id)[0].prefix)

    def test_edge_source_has_correct_metadata(self):
        # 2111 is VLAN.id
        metadata = self.netmap_graph.get_edge_data(self.a, self.b)
        source = metadata.get('metadata').get(2111)[0].source
        self.assertEqual(source.interface, self.a1)
        self.assertEqual(source.netbox, self.a)
        self.assertEqual(source.gw_ip, '158.38.0.1')
        self.assertFalse(source.virtual)

    def test_edge_target_has_correct_metadata(self):
        metadata = self.netmap_graph.get_edge_data(self.a, self.b)
        target = metadata.get('metadata').get(2111)[0].target
        self.assertEqual(target.interface, self.b1)
        self.assertEqual(target.netbox, self.b)
        self.assertEqual(target.gw_ip, '158.38.0.2')
        self.assertFalse(target.virtual)

    def test_uplink_has_all_layer3_properties_it_should_for_source(self):
        should_have = ('gw_ip', 'virtual')

        for edge in self.netmap_graph.get_edge_data(self.a, self.b).get('metadata').get(2111):
            self.assertTrue(
                all([hasattr(edge.source, attribute) for attribute in should_have]),
                msg="Didn't find all keys {0}, only found: {1}".format(
                    should_have,
                    edge.__dict__.keys()
                )
            )

    def test_uplink_has_all_layer3_properties_it_should_for_target(self):
        should_have = ('gw_ip', 'virtual')

        for edge in self.netmap_graph.get_edge_data(self.a, self.b).get('metadata').get(
            2111):
            self.assertTrue(
                all([hasattr(edge.target, attribute) for attribute in should_have]),
                msg="Didn't find all keys {0}, only found: {1}".format(
                    should_have,
                    edge.__dict__.keys()
                )
            )

    def test_uplink_has_all_layer3_properties_it_should(self):
        should_have = ('prefix', 'vlan')

        for edge in self.netmap_graph.get_edge_data(self.a, self.b).get('metadata').get(2111):
            self.assertTrue(
                all(
                    [hasattr(edge, y) for y in should_have]
                ),
                msg="Didn't find all keys {0}, only found: {1}".format(
                should_have,
                edge.__dict__.keys()
            ))
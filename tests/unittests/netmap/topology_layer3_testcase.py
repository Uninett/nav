from mock import patch
import networkx as nx
from nav.models.manage import Prefix, Vlan, GwPortPrefix, NetType
from nav.netmap import topology, stubs
from nav.topology import vlan
from .topology_testcase import TopologyTestCase


class TopologyLayer3TestCase(TopologyTestCase):
    def setUp(self):
        """
        Build a graph with the following network:

        node a and node b connected with a linknet prefix 158.38.0.0/30
         with it's first pair of interfaces {a1: 1, b1: 2}
        node a and node c connected with a linknet prefix 158.38.0.4/30
         with it's second pair of interfaces {a3: 5, c3: 6}
        node b and node d and node e connected as a core linknet on prefix
         158.38.1.0/29  {b4: 1, d4: 2, , e4: 3}
        node f connected to unknown node (elink) as a linknet on prefix
         158.38.99.0/30 { f5: 1, UNKNOWN }
        """
        super(TopologyLayer3TestCase, self).setUp()

        self.model_id = 1
        self.nav_graph = nx.MultiGraph()

        self.net_type_link = NetType(id=1, description='link')
        self.net_type_elink = NetType(id=2, description='elink')
        self.net_type_core = NetType(id=3, description='core')

        self.a = a = self._netbox_factory('a')
        self.b = b = self._netbox_factory('b')
        self.c = c = self._netbox_factory('c')
        self.d = d = self._netbox_factory('d')
        self.e = e = self._netbox_factory('e')
        self.f = f = self._netbox_factory('f')

        self.a1 = a1 = self._interface_factory('a1', a)
        self.a3 = a3 = self._interface_factory('a3', a)

        self.b1 = b1 = self._interface_factory('b1', b)
        self.b4 = b4 = self._interface_factory('b4', b)

        self.c3 = c3 = self._interface_factory('c3', c)

        self.d4 = d4 = self._interface_factory('d4', d)

        self.e4 = e4 = self._interface_factory('e4', e)

        self.f5 = f5 = self._interface_factory('f5', f)

        self.prefix_foo = Prefix(
            id=1111,
            net_address="158.38.0.0/30",
            vlan=Vlan(id=2111, vlan=50, net_type=self.net_type_link),
        )

        self.prefix_bar_vlan = Vlan(id=2112, vlan=50, net_type=self.net_type_link)
        self.prefix_bar = Prefix(
            id=1112, net_address="158.38.0.4/30", vlan=self.prefix_bar_vlan
        )
        self.prefix_bar_ipv6 = Prefix(
            id=6112, net_address="feed:dead:cafe:babe::/64", vlan=self.prefix_bar_vlan
        )

        self.prefix_baz = Prefix(
            id=1113,
            net_address="158.38.1.0/29",
            vlan=Vlan(id=2113, vlan=50, net_type=self.net_type_core),
        )
        self.prefix_zar = Prefix(
            id=1114,
            net_address="158.38.99.0/30",
            vlan=Vlan(id=2114, vlan=50, net_type=self.net_type_elink),
        )

        # fictive netbox, interface, gwportprefix for F to UNKNOWN
        self.unknown = unknown = stubs.Netbox()
        unknown.sysname = 'fictive netbox'
        unknown.category_id = 'elink'

        self.unknown_interface = unknown_interface = stubs.Interface()
        self.unknown_interface.netbox = unknown
        self.unknown_interface.ifname = "?"
        self.unknown_interface.speed = None

        # node a and node b connected with a linknet prefix 158.38.0.0/30
        # with it's first pair of interfaces {a1: 1, b1: 2}
        self.linknet_a1_for_a_b = GwPortPrefix(
            interface=self.a1, prefix=self.prefix_foo, gw_ip='158.38.0.1', virtual=False
        )
        self.linknet_b1_for_a_b = GwPortPrefix(
            interface=self.b1, prefix=self.prefix_foo, gw_ip='158.38.0.2', virtual=False
        )

        self._add_edge(
            self.nav_graph,
            self.linknet_a1_for_a_b,
            self.linknet_b1_for_a_b,
            self.prefix_foo,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_b1_for_a_b,
            self.linknet_a1_for_a_b,
            self.prefix_foo,
        )

        # node a and node c connected with a linknet prefix 158.38.0.4/30
        # with it's second pair of interfaces {a2: 5, c2: 6}
        self.linknet_a3_for_a_c = GwPortPrefix(
            interface=self.a3, prefix=self.prefix_bar, gw_ip='158.38.0.5', virtual=False
        )
        self.linknet_c3_for_a_c = GwPortPrefix(
            interface=self.c3, prefix=self.prefix_bar, gw_ip='158.38.0.6', virtual=False
        )
        self.linknet_v6_a3_for_a_c = GwPortPrefix(
            interface=self.a3,
            prefix=self.prefix_bar_ipv6,
            gw_ip='feed:dead:cafe:babe::5',
            virtual=False,
        )
        self.linknet_v6_c3_for_a_c = GwPortPrefix(
            interface=self.c3,
            prefix=self.prefix_bar_ipv6,
            gw_ip='feed:dead:cafe:babe::3',
            virtual=False,
        )

        # v4 prefix
        self._add_edge(
            self.nav_graph,
            self.linknet_a3_for_a_c,
            self.linknet_c3_for_a_c,
            self.prefix_bar,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_c3_for_a_c,
            self.linknet_a3_for_a_c,
            self.prefix_bar,
        )
        # v6 prefix
        self._add_edge(
            self.nav_graph,
            self.linknet_v6_a3_for_a_c,
            self.linknet_v6_c3_for_a_c,
            self.prefix_bar_ipv6,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_v6_c3_for_a_c,
            self.linknet_v6_a3_for_a_c,
            self.prefix_bar_ipv6,
        )

        # node b and node d and node e connected as a core linknet on prefix
        # 158.38.1.0/29  {b3: 1, d3: 2, , e3: 3}
        self.linknet_b4_for_b_d_e = GwPortPrefix(
            interface=self.b4, prefix=self.prefix_baz, gw_ip='158.38.1.1', virtual=False
        )
        self.linknet_d4_for_b_d_e = GwPortPrefix(
            interface=self.d4, prefix=self.prefix_baz, gw_ip='158.38.1.2', virtual=False
        )
        self.linknet_e4_for_b_d_e = GwPortPrefix(
            interface=self.e4, prefix=self.prefix_baz, gw_ip='158.38.1.3', virtual=False
        )

        # core is a STAR.
        # b3, d3
        self._add_edge(
            self.nav_graph,
            self.linknet_b4_for_b_d_e,
            self.linknet_d4_for_b_d_e,
            self.prefix_baz,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_b4_for_b_d_e,
            self.linknet_e4_for_b_d_e,
            self.prefix_baz,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_d4_for_b_d_e,
            self.linknet_b4_for_b_d_e,
            self.prefix_baz,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_d4_for_b_d_e,
            self.linknet_e4_for_b_d_e,
            self.prefix_baz,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_e4_for_b_d_e,
            self.linknet_b4_for_b_d_e,
            self.prefix_baz,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_e4_for_b_d_e,
            self.linknet_d4_for_b_d_e,
            self.prefix_baz,
        )

        # node f connected to unknown node (elink) as a linknet on prefix
        # 158.38.99.0/30 { f4: 1, UNKNOWN }
        self.linknet_f5_for_f_unknown = GwPortPrefix(
            interface=self.f5,
            prefix=self.prefix_zar,
            gw_ip='158.38.99.1',
            virtual=False,
        )
        self.linknet_unknown4_for_f_unknown = stubs.GwPortPrefix()
        self.linknet_unknown4_for_f_unknown.interface = unknown_interface
        self.linknet_unknown4_for_f_unknown.gw_ip = unknown.sysname
        self.linknet_unknown4_for_f_unknown.prefix = self.prefix_zar

        self._add_edge(
            self.nav_graph,
            self.linknet_f5_for_f_unknown,
            self.linknet_unknown4_for_f_unknown,
            self.prefix_zar,
        )
        self._add_edge(
            self.nav_graph,
            self.linknet_unknown4_for_f_unknown,
            self.linknet_f5_for_f_unknown,
            self.prefix_zar,
        )

        self.vlans = patch.object(
            topology,
            '_get_vlans_map_layer3',
            return_value={
                2111: [self.prefix_foo],
                2112: [self.prefix_bar, self.prefix_bar_ipv6],
                2113: [self.prefix_baz],
                2114: [self.prefix_zar],
            },
        )
        self.vlans.start()

        self.l3 = patch.object(vlan, 'build_layer3_graph', return_value=self.nav_graph)
        self.l3.start()

        self.netmap_graph = topology.build_netmap_layer3_graph(self.nav_graph, None)

    def tearDown(self):
        self.vlans.stop()
        self.l3.stop()

    def _add_edge(self, graph, netbox_a, netbox_b, prefix):
        graph.add_edge(netbox_a, netbox_b, key=prefix)

    def test_noop_layer3_testcase_setup(self):
        self.assertTrue(True)

    def test_noop_setup_netmap_graph_layer3(self):
        self.assertTrue(self.netmap_graph)

from mock import patch
import networkx as nx
from nav.models.manage import SwPortVlan, Vlan
from nav.netmap import topology
from nav.topology import vlan
from .topology_testcase import TopologyTestCase


class TopologyLayer2TestCase(TopologyTestCase):
    def setUp(self):
        super(TopologyLayer2TestCase, self).setUp()

        self.model_id = 1
        self.nav_graph = nx.MultiDiGraph()

        self.a = a = self._netbox_factory('a')
        self.b = b = self._netbox_factory('b')
        self.c = c = self._netbox_factory('c')
        self.d = d = self._netbox_factory('d')

        self.a1 = a1 = self._interface_factory('a1', a)
        self.a2 = a2 = self._interface_factory('a2', a)
        self.a3 = a3 = self._interface_factory('a3', a)
        self.b1 = b1 = self._interface_factory('b1', b)
        self.b2 = b2 = self._interface_factory('b2', b)
        self.c3 = c3 = self._interface_factory('c3', c)
        self.c4 = c4 = self._interface_factory('c4', c)
        self.d4 = d4 = self._interface_factory('d4', d)

        self._add_edge(self.nav_graph, a1.netbox, a1, b1.netbox, b1)
        self._add_edge(self.nav_graph, b1.netbox, b1, a1.netbox, a1)
        self._add_edge(self.nav_graph, a2.netbox, a2, b2.netbox, b2)
        self._add_edge(self.nav_graph, b2.netbox, b2, a2.netbox, a2)
        self._add_edge(self.nav_graph, a3.netbox, a3, c3.netbox, c3)
        self._add_edge(self.nav_graph, d4.netbox, d4, c4.netbox, c4)

        self.vlan__a1_b1 = a_vlan_between_a1_and_b1 = SwPortVlan(
            id=self._next_id(), interface=self.a1, vlan=Vlan(id=201, vlan=2)
        )

        self.vlans = patch.object(
            topology,
            '_get_vlans_map_layer2',
            return_value=(
                {
                    self.a1: [a_vlan_between_a1_and_b1],
                    self.b1: [a_vlan_between_a1_and_b1],
                    self.a2: [],
                    self.b2: [],
                    self.a3: [],
                    self.c3: [],
                },
                {
                    self.a: {201: a_vlan_between_a1_and_b1},
                    self.b: {201: a_vlan_between_a1_and_b1},
                    self.c: {},
                },
            ),
        )
        self.vlans.start()

        self.build_l2 = patch.object(
            vlan, 'build_layer2_graph', return_value=self.nav_graph
        )
        self.build_l2.start()

        bar = vlan.build_layer2_graph()
        # foo = topology._get_vlans_map_layer2(bar)

        vlan_by_interfaces, vlan_by_netbox = topology._get_vlans_map_layer2(
            self.nav_graph
        )

        self.netmap_graph = topology.build_netmap_layer2_graph(
            vlan.build_layer2_graph(), vlan_by_interfaces, vlan_by_netbox, None
        )

    def tearDown(self):
        self.vlans.stop()
        self.build_l2.stop()

    def test_noop_layer2_testcase_setup(self):
        self.assertTrue(True)

    def _add_edge(self, g, node_a, interface_a, node_b, interface_b):
        interface_a.to_interface = interface_b
        g.add_edge(node_a, node_b, key=interface_a)

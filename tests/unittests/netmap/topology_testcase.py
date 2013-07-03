import unittest
import networkx as nx
from nav.models.manage import Netbox, Interface

class TopologyTestCase(unittest.TestCase):
    def _next_id(self):
        self.model_id = self.model_id+1
        return self.model_id

    def _netbox_factory(self, sysname, interface=None):
        netbox = Netbox()
        netbox.id = self._next_id()
        netbox.sysname = sysname
        netbox.interface = interface
        return netbox

    def _interface_factory(self, ifname, netbox):
        interface = Interface()
        interface.id = self._next_id()
        interface.ifname = ifname
        if netbox and isinstance(netbox, Netbox):
            interface.netbox = netbox
        elif netbox:
            interface.netbox = self._netbox_factory(netbox, interface)
        return interface

    def _add_edge(self, g, node_a, interface_a, node_b, interface_b):
        interface_a.to_interface = interface_b
        g.add_edge(node_a, node_b, key=interface_a)

    def setUp(self):
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

    def test_noop_setup(self):
        self.assertTrue(True)


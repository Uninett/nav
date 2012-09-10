import unittest
import networkx as nx
from nav.models.manage import Netbox, Interface

class NetmapGraphTestCase(unittest.TestCase):
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

    def setUp(self):
        self.model_id = 1
        self.graph = nx.MultiDiGraph(name="Graph")

        netbox_a = self._netbox_factory('unittest.a.nav')
        netbox_b = self._netbox_factory("unittest.b.nav")

        #int_a_1 = self._interface_factory('1', 'unittest.a.nav')
        int_a_1 = self._interface_factory('1', netbox_a)

        #int_b_1 = self._interface_factory('1', 'unittest.b.nav')
        int_b_1 = self._interface_factory('1', netbox_b)

        #int_a_1.to_interface = self._interface_factory('1', 'unittest.b.nav')
        #int_b_1.to_interface = self._interface_factory('1', 'unittest.a.nav')

        int_a_1.to_interface = self._interface_factory('1', netbox_b)
        int_b_1.to_interface = self._interface_factory('1', netbox_a)


        self.assertNotEquals(netbox_a.id, netbox_b.id)
        self.assertNotEquals(int_a_1.id, int_b_1.id)
        self.assertNotEquals(int_a_1.to_interface.id, int_b_1.to_interface.id)

        self.graph.add_edge(int_b_1.netbox, int_b_1.to_interface.netbox,
            key=int_b_1
            , metadata={'thiss': [int_b_1.netbox, int_b_1],'other': [int_a_1.netbox, int_a_1]})

        self.graph.add_edge(int_a_1.netbox, int_a_1.to_interface.netbox,
            key=int_a_1
            , metadata={'thiss': [int_a_1.netbox, int_a_1],'other': [int_b_1.netbox, int_b_1]})


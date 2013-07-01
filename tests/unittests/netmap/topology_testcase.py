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

    def _meta_edge(self, node_a, interface_a, node_b, interface_b):
        return {
            'uplink': {
                'thiss': {
                    'interface': interface_a,
                    'netbox': node_a,
                    'netbox_link': '/ipdevinfo/' + node_a.sysname,
                    'interface_link': '/ipdevinfo/' + node_a.sysname + '/interface=' +
                                      interface_a.ifname
                },
                'other': {
                    'interface': interface_b,
                    'netbox': node_b,
                    'netbox_link': '/ipdevinfo/' + node_b.sysname,
                    'interface_link': '/ipdevinfo/' + node_b.sysname + '/interface=' +
                        interface_b.ifname
                }
            },
            'links': [interface_a.ifname + '-' + interface_b.ifname]
        }

    def _add_edge(self, g, node_a, interface_a, node_b, interface_b):
        g.add_edge(node_a, node_b, key=interface_a, attr_dict=
        self._meta_edge(node_a, interface_a, node_b, interface_b)
        )

    def setUp(self):
        self.model_id = 1
        self.nav_graph = nx.MultiDiGraph(name="Graph")

        # keeping interface id related to switch port, so easier to
        # visualized graph in your head.

        #      a(1) <-> b(1)
        #      b(2) <-> c(2)
        #      b(3) <-> c(3)
        #      b(4) <-> d(4)
        #      d(5) <-> a(5)
        #
        netbox_a = self._netbox_factory("unittest.a.nav")
        netbox_b = self._netbox_factory("unittest.b.nav")
        netbox_c = self._netbox_factory("unittest.c.nav")
        netbox_d = self._netbox_factory("unittest.d.nav")

        # ports for netbox A
        int_a_1 = self._interface_factory('1', netbox_a)
        int_a_5 = self._interface_factory('5', netbox_a)

        # ports for netbox B
        int_b_1 = self._interface_factory('1', netbox_b)
        int_b_2 = self._interface_factory('2', netbox_b)
        int_b_3 = self._interface_factory('3', netbox_b)
        int_b_4 = self._interface_factory('4', netbox_b)

        # ports for netbox C
        int_c_2 = self._interface_factory('2', netbox_c)
        int_c_3 = self._interface_factory('3', netbox_c)

        # ports for netbox D
        int_d_4 = self._interface_factory('4', netbox_d)
        int_d_5 = self._interface_factory('5', netbox_d)

        # a(1) <-> b(1)
        int_a_1.to_interface = self._interface_factory('1', 'unittest.b.nav')
        int_b_1.to_interface = self._interface_factory('1', 'unittest.a.nav')

        # b(2) <-> c(2)
        int_b_2.to_interface = self._interface_factory('2', 'unittest.c.nav')
        int_c_2.to_interface = self._interface_factory('2', 'unittest.b.nav')

        # b(3) <-> c(3)
        int_b_3.to_interface = self._interface_factory('3', 'unittest.c.nav')
        int_c_3.to_interface = self._interface_factory('3', 'unittest.b.nav')

        # b(4) <-> d(4)
        int_b_4.to_interface = self._interface_factory('4', 'unittest.d.nav')
        int_d_4.to_interface = self._interface_factory('4', 'unittest.b.nav')

        # d(5) <-> a(5)
        int_d_5.to_interface = self._interface_factory('5', 'unittest.a.nav')
        int_a_5.to_interface = self._interface_factory('5', 'unittest.d.nav')


        self.assertNotEquals(netbox_a.id, netbox_b.id)
        self.assertNotEquals(int_a_1.id, int_b_1.id)
        self.assertNotEquals(int_a_1.to_interface.id, int_b_1.to_interface.id)

        def _add_edge_both_ways(a_interface, b_interface):
            self.nav_graph.add_edge(a_interface.netbox, a_interface.to_interface.netbox,
                                key=a_interface,
                                metadata={
                                    'thiss': [a_interface.netbox, a_interface],
                                    'other': [b_interface.netbox, b_interface]
                                })
            self.nav_graph.add_edge(b_interface.netbox, b_interface.to_interface.netbox,
                                key=b_interface,
                                metadata={
                                    'thiss': [b_interface.netbox, b_interface],
                                    'other': [a_interface.netbox, a_interface]
                                })

        #      a(1) <-> b(1)
        _add_edge_both_ways(int_a_1, int_b_1)

        #      b(2) <-> c(2)
        _add_edge_both_ways(int_b_2, int_c_2)

        #      b(3) <-> c(3)
        _add_edge_both_ways(int_b_3, int_c_3)

        #      b(4) <-> d(4)
        _add_edge_both_ways(int_b_4, int_d_4)

        #      d(5) <-> a(5)
        _add_edge_both_ways(int_d_5, int_a_5)

    def test_noop_setup(self):
        self.assertTrue(True)


import datetime

from nav.models.manage import Netbox, Device, Room, Category, Organization
from nav.models.manage import NetType, Vlan, Prefix, Interface, SwPortVlan
from nav.models.manage import Arp, Cam, GwPortPrefix
from mock import patch

from nav.web import l2trace
from nav.tests.cases import DjangoTransactionTestCase

class L2TraceTestCase(DjangoTransactionTestCase):
    fixtures = ['l2trace_fixture.xml']

    def setUp(self):
        super(L2TraceTestCase, self).setUp()
        # Mock the DNS lookup methods; none of the test addresses will
        # resolve, they will just cause the tests to take a long time
        self.get_host_by_name = patch('l2trace.Host.get_host_by_name',
                                      return_value=None)
        self.get_host_by_addr = patch('l2trace.Host.get_host_by_addr',
                                      return_value = None)
        self.get_host_by_name.start()
        self.get_host_by_addr.start()

        self.foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        self.foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        self.employee_vlan = Vlan.objects.get(net_ident='employeevlan')
        self.admin_vlan = Vlan.objects.get(net_ident='adminvlan')

    def tearDown(self):
        self.get_host_by_name.stop()
        self.get_host_by_addr.stop()

class GetVlanFromThingsTest(L2TraceTestCase):
    def test_arbitrary_ip_is_on_vlan_10(self):
        vlan = l2trace.get_vlan_from_ip('10.0.0.99')
        self.assertTrue(vlan is not None)
        self.assertEquals(vlan.vlan, 10)
        self.assertEquals(vlan.net_ident, 'adminvlan')

    def test_router_is_on_vlan_10(self):
        host = l2trace.Host('10.0.0.1')
        vlan = l2trace.get_vlan_from_host(host)
        self.assertTrue(vlan is not None)
        self.assertEquals(vlan.vlan, 10)
        self.assertEquals(vlan.net_ident, 'adminvlan')

    def test_switch_is_on_vlan_10(self):
        vlan = l2trace.get_netbox_vlan(self.foo_sw1)

        self.assertTrue(vlan is not None)
        self.assertEquals(vlan.vlan, 10)
        self.assertEquals(vlan.net_ident, 'adminvlan')


class NetboxFromHostTest(L2TraceTestCase):
    def test_known_ip_is_router(self):
        host = l2trace.Host('10.0.0.1')
        found = l2trace.get_netbox_from_host(host)
        self.assertTrue(found is not None)
        self.assertEquals(found.sysname, 'foo-gw.example.org')

    def test_unknown_ip_gives_none_as_result(self):
        unknown_host = l2trace.Host('10.0.0.99')
        self.assertTrue(l2trace.get_netbox_from_host(unknown_host) is None)

    def test_known_ip_is_netbox(self):
        h = l2trace.get_host_or_netbox_from_addr('10.0.0.1')
        self.assertTrue(hasattr(h, 'sysname'))
        self.assertEquals(h.sysname, 'foo-gw.example.org')

    def test_unknown_ip_is_host(self):
        ip = '10.99.99.99'
        h = l2trace.get_host_or_netbox_from_addr(ip)
        self.assertTrue(hasattr(h, 'hostname'))
        self.assertEquals(h.hostname, ip)

class GatewayTests(L2TraceTestCase):
    def test_foo_gw_is_router_for_employee_vlan(self):
        self.assertEquals(
            l2trace.get_vlan_gateway(self.employee_vlan),
            self.foo_gw)

    def test_foo_gw_is_router_for_admin_vlan(self):
        self.assertEquals(
            l2trace.get_vlan_gateway(self.admin_vlan),
            self.foo_gw)

    def test_foo_gw_is_router(self):
        self.assertTrue(l2trace.is_netbox_gateway(self.foo_gw))

    def test_foo_sw1_is_not_a_router(self):
        self.assertFalse(l2trace.is_netbox_gateway(self.foo_sw1))


class VlanEqualityTests(L2TraceTestCase):
    def test_ips_should_be_on_same_vlan(self):
        self.assertTrue(l2trace.are_hosts_on_same_vlan('10.0.0.1', '10.0.0.2'))

    def test_ips_should_not_be_on_same_vlan(self):
        self.assertFalse(l2trace.are_hosts_on_same_vlan('10.0.20.1', '10.0.0.2'))

class DownlinkTests(L2TraceTestCase):
    def test_employee1_downlink_should_be_foo_sw1_gi_0_10(self):
        host = l2trace.Host('10.0.20.10')
        host.hostname = 'employee10.example.org'

        swpvlan = l2trace.get_vlan_downlink_to_host(host)
        self.assertTrue(swpvlan is not None)
        self.assertEquals(swpvlan.interface.ifname, 'Gi0/10')
        self.assertEquals(swpvlan.interface.netbox, self.foo_sw1)
        self.assertEquals(swpvlan.vlan.vlan, 20)

    def test_foo_sw1_vlan_downlink_should_be_on_foo_gw_gi_0_13(self):
        swpvlan = l2trace.get_vlan_downlink_to_netbox(self.foo_sw1)
        self.assertTrue(swpvlan is not None)
        self.assertEquals(swpvlan.vlan.vlan, 10)
        self.assertEquals(swpvlan.interface.ifname, 'Gi0/13')
        self.assertEquals(swpvlan.interface.netbox, self.foo_gw)

    def test_foo_sw1_employee_vlan_uplink_should_be_foo_gw_gi_0_13(self):
        swpvlan = l2trace.get_vlan_downlink_to_netbox(self.foo_sw1,
                                                      self.employee_vlan)
        self.assertTrue(swpvlan is not None)
        self.assertEquals(swpvlan.vlan.vlan, 20)
        self.assertEquals(swpvlan.interface.ifname, 'Gi0/13')
        self.assertEquals(swpvlan.interface.netbox, self.foo_gw)

class UplinkTests(L2TraceTestCase):
    def test_foo_sw1_vlan_uplink_should_be_gi_0_1(self):
        swpvlan = l2trace.get_vlan_uplink_from_netbox(self.foo_sw1)
        self.assertTrue(swpvlan is not None)
        self.assertEquals(swpvlan.vlan.vlan, 10)
        self.assertEquals(swpvlan.interface.ifname, 'Gi0/1')

    def test_foo_sw1_employee_vlan_uplink_should_be_gi_0_1(self):
        vlan = self.employee_vlan
        swpvlan = l2trace.get_vlan_uplink_from_netbox(self.foo_sw1,
                                                      vlan)
        self.assertTrue(swpvlan is not None)
        self.assertEquals(swpvlan.vlan, vlan)
        self.assertEquals(swpvlan.interface.ifname, 'Gi0/1')

class HostTests(L2TraceTestCase):
    def test_host_without_resolvable_name(self):
        ip = '10.99.99.99'
        h = l2trace.Host(ip)
        self.assertEquals(h.host, ip)
        self.assertEquals(h.ip, ip)
        self.assertEquals(h.hostname, ip)

    def test_hosts_are_equal(self):
        host1 = l2trace.Host('10.99.99.99')
        host2 = l2trace.Host('10.99.99.99')
        self.assertEquals(host1, host2)

    def test_host_with_host_argument_returns_equal_instance(self):
        host1 = l2trace.Host('10.99.99.99')
        host2 = l2trace.Host(host1)
        self.assertEquals(host1, host2)


class StartPathTests(L2TraceTestCase):
    def test_start_path_for_foo_sw1_ip_should_be_on_vlan_10(self):
        node = l2trace.get_start_path('10.0.0.11')
        self.assertTrue(node is not None)
        self.assertEquals(node.vlan.vlan, 10)
        self.assertTrue(node.if_in is None)
        self.assertTrue(isinstance(node.host, Netbox))
        self.assertEquals(node.host.sysname, 'foo-sw1.example.org')


    def test_start_path_for_employee1_should_be_on_vlan_20(self):
        ip = '10.0.20.10'
        node = l2trace.get_start_path(ip)
        self.assertTrue(node is not None)
        self.assertEquals(node.vlan.vlan, 20)
        self.assertTrue(node.if_in is None)
        self.assertTrue(isinstance(node.host, l2trace.Host))
        self.assertEquals(node.host.hostname, ip)
        self.assertTrue(node.if_out is None)


class PathTests(L2TraceTestCase):
    def test_path_for_foo_sw1_should_be_2_long(self):
        path = l2trace.get_path(self.foo_sw1.ip)
        self.assertEquals(len(path), 2)

    def test_path_for_foo_sw1_should_start_with_foo_sw1(self):
        path = l2trace.get_path(self.foo_sw1.ip)
        self.assertEquals(path[0].host, self.foo_sw1)

    def test_path_for_foo_sw1_should_end_at_foo_gw(self):
        path = l2trace.get_path(self.foo_sw1.ip)
        self.assertEquals(path[-1].host, self.foo_gw)

    def test_path_for_foo_sw1_should_be_on_vlan_10(self):
        path = l2trace.get_path(self.foo_sw1.ip)
        self.assertEquals(path[0].vlan.vlan, 10)
        self.assertEquals(path[1].vlan.vlan, 10)

    def test_path_for_employee1_should_be_3_long(self):
        path = l2trace.get_path('10.0.20.10')
        self.assertEquals(len(path), 3)

    def test_path_for_employee2_should_be_3_long(self):
        path = l2trace.get_path('10.0.20.90')
        self.assertEquals(len(path), 3, path)

    def test_path_for_employee1_should_be_on_vlan_20(self):
        path = l2trace.get_path('10.0.20.10')
        self.assertEquals(path[0].vlan.vlan, 20)
        self.assertEquals(path[1].vlan.vlan, 20)

    def test_path_for_employee1_should_start_with_employee_1(self):
        path = l2trace.get_path('10.0.20.10')
        self.assertTrue(isinstance(path[0].host, l2trace.Host))

    def test_path_for_employee1_should_end_with_foo_gw(self):
        path = l2trace.get_path('10.0.20.10')
        self.assertEquals(path[-1].host, self.foo_gw)

class TraceTests(L2TraceTestCase):
    def test_make_rows_returns_generator(self):
        l = l2trace.L2TraceQuery('10.0.20.10', '')
        l.trace()
        generator = l.make_rows()
        self.assertTrue(hasattr(generator, 'next'))

    def test_make_rows_generates_result_rows(self):
        l = l2trace.L2TraceQuery('10.0.20.10', '')
        l.trace()
        generator = l.make_rows()
        first = generator.next()
        self.assertTrue(isinstance(first, l2trace.ResultRow))

    def test_first_row_is_host_from(self):
        ip = '10.0.20.10'
        l = l2trace.L2TraceQuery(ip, '')
        l.trace()
        first_row = l.make_rows().next()
        self.assertEquals(first_row.sysname, ip)

    def test_first_and_last_rows_match_hosts(self):
        ip1 = '10.0.20.10'
        ip2 = '10.0.20.90'
        l = l2trace.L2TraceQuery(ip1, ip2)
        l.trace()
        rows = list(l.make_rows())
        self.assertEquals(rows[0].sysname, ip1, l.path)
        self.assertEquals(rows[-1].sysname, ip2, l.path)

    def test_employee_path_passes_through_foo_sw1(self):
        ip1 = '10.0.20.10'
        ip2 = '10.0.20.90'
        l = l2trace.L2TraceQuery(ip1, ip2)
        l.trace()
        rows = list(l.make_rows())
        self.assertEquals(len(rows), 3, rows)
        switch_row = rows[1]

        self.assertEquals(switch_row.sysname, 'foo-sw1.example.org')

    def test_should_not_fail_on_invalid_hosts(self):
        l = l2trace.L2TraceQuery('s;dfl', '923urfk\';')
        l.trace()
        rows = list(l.make_rows())


class JunctionTests(L2TraceTestCase):
    def setUp(self):
        super(JunctionTests, self).setUp()
        Host = l2trace.Host
        self.from_path = [
            l2trace.PathNode(None, None, Host('10.0.20.10'), None),
            l2trace.PathNode(None, None, self.foo_sw1, None),
            l2trace.PathNode(None, None, self.foo_gw, None),
            ]

        self.to_path = [
            l2trace.PathNode(None, None, self.foo_gw, None),
            l2trace.PathNode(None, None, self.foo_sw1, None),
            l2trace.PathNode(None, None, Host('10.0.20.90'), None),
            ]

    def test_find_junction_should_return_same_host(self):
        (node1, node2) = l2trace.find_junction(self.from_path, self.to_path)
        self.assertEquals(node1.host, node2.host)

    def test_find_junction_should_return_foo_sw1(self):
        (node1, node2) = l2trace.find_junction(self.from_path, self.to_path)
        self.assertEquals(node1.host, self.foo_sw1)
        self.assertEquals(node2.host, self.foo_sw1)

    def test_find_junction_should_return_nodes_from_paths(self):
        (from_node, to_node) = l2trace.find_junction(self.from_path,
                                                     self.to_path)
        self.assertTrue(from_node in self.from_path)
        self.assertTrue(to_node in self.to_path)

    def test_join_at_junction_should_be_3_long(self):
        new_path = l2trace.join_at_junction(self.from_path, self.to_path)
        self.assertEquals(len(new_path), 3, new_path)

    def test_joined_path_should_start_and_end_with_correct_hosts(self):
        new_path = l2trace.join_at_junction(self.from_path, self.to_path)
        self.assertEquals(new_path[0], self.from_path[0])
        self.assertEquals(new_path[-1], self.to_path[-1])


from nav.tests.cases import ModPythonTestCase
from django.test.client import Client

class L2TraceWebTest(L2TraceTestCase, ModPythonTestCase):
    module_under_test = l2trace

    def test_l2trace_without_args_shoule_be_ok(self):
        client = Client()
        response = client.get('/l2trace/')
        self.assertEquals(response.status_code, 200)

    def test_l2trace_with_args_should_be_ok(self):
        client = Client()
        response = client.get('/l2trace/', {'host_from': '10.0.20.10',
                                            'host_to': '10.0.20.90'})
        self.assertEquals(response.status_code, 200)

    def test_l2trace_with_unknown_ip_args_should_be_ok(self):
        client = Client()
        response = client.get('/l2trace/', {'host_from': '192.168.1.1',
                                            'host_to': '192.168.10.12'})
        self.assertEquals(response.status_code, 200)

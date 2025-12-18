"""Integration tests for nav.web.l2trace"""

import types
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from nav.models.manage import (
    Arp,
    Cam,
    GwPortPrefix,
    Interface,
    Location,
    Netbox,
    Organization,
    Prefix,
    Room,
    SwPortVlan,
    Vlan,
)
from nav.web import l2trace


###
#
# Test Classes
#
###


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestGetVlanFromThings:
    def test_arbitrary_ip_is_on_vlan_10(self, l2trace_topology):
        vlan = l2trace.get_vlan_from_ip('10.0.0.99')
        assert vlan is not None
        assert vlan.vlan == 10
        assert vlan.net_ident == 'adminvlan'

    def test_router_is_on_vlan_10(self, l2trace_topology):
        host = l2trace.Host('10.0.0.1')
        vlan = l2trace.get_vlan_from_host(host)
        assert vlan is not None
        assert vlan.vlan == 10
        assert vlan.net_ident == 'adminvlan'

    def test_switch_is_on_vlan_10(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        vlan = l2trace.get_netbox_vlan(foo_sw1)
        assert vlan is not None
        assert vlan.vlan == 10
        assert vlan.net_ident == 'adminvlan'


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestNetboxFromHost:
    def test_known_ip_is_router(self, l2trace_topology):
        host = l2trace.Host('10.0.0.1')
        found = l2trace.get_netbox_from_host(host)
        assert found is not None
        assert found.sysname == 'foo-gw.example.org'

    def test_unknown_ip_gives_none_as_result(self, l2trace_topology):
        unknown_host = l2trace.Host('10.0.0.99')
        assert l2trace.get_netbox_from_host(unknown_host) is None

    def test_known_ip_is_netbox(self, l2trace_topology):
        h = l2trace.get_host_or_netbox_from_addr('10.0.0.1')
        assert hasattr(h, 'sysname')
        assert h.sysname == 'foo-gw.example.org'

    def test_unknown_ip_is_host(self, l2trace_topology):
        ip = '10.99.99.99'
        h = l2trace.get_host_or_netbox_from_addr(ip)
        assert hasattr(h, 'hostname')
        assert h.hostname == ip


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestGateway:
    def test_foo_gw_is_router_for_employee_vlan(self, l2trace_topology):
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        employee_vlan = Vlan.objects.get(net_ident='employeevlan')
        assert l2trace.get_vlan_gateway(employee_vlan) == foo_gw

    def test_foo_gw_is_router_for_admin_vlan(self, l2trace_topology):
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        admin_vlan = Vlan.objects.get(net_ident='adminvlan')
        assert l2trace.get_vlan_gateway(admin_vlan) == foo_gw

    def test_foo_gw_is_router(self, l2trace_topology):
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        assert l2trace.is_netbox_gateway(foo_gw)

    def test_foo_sw1_is_not_a_router(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        assert not l2trace.is_netbox_gateway(foo_sw1)


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestVlanEquality:
    def test_ips_should_be_on_same_vlan(self, l2trace_topology):
        assert l2trace.are_hosts_on_same_vlan('10.0.0.1', '10.0.0.2')

    def test_ips_should_not_be_on_same_vlan(self, l2trace_topology):
        assert not l2trace.are_hosts_on_same_vlan('10.0.20.1', '10.0.0.2')


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestDownlink:
    def test_employee1_downlink_should_be_foo_sw1_gi_0_10(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        host = l2trace.Host('10.0.20.10')
        host.hostname = 'employee10.example.org'

        swpvlan = l2trace.get_vlan_downlink_to_host(host)
        assert swpvlan is not None
        assert swpvlan.interface.ifname == 'Gi0/10'
        assert swpvlan.interface.netbox == foo_sw1
        assert swpvlan.vlan.vlan == 20

    def test_foo_sw1_vlan_downlink_should_be_on_foo_gw_gi_0_13(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')

        swpvlan = l2trace.get_vlan_downlink_to_netbox(foo_sw1)
        assert swpvlan is not None
        assert swpvlan.vlan.vlan == 10
        assert swpvlan.interface.ifname == 'Gi0/13'
        assert swpvlan.interface.netbox == foo_gw

    def test_foo_sw1_employee_vlan_uplink_should_be_foo_gw_gi_0_13(
        self, l2trace_topology
    ):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        employee_vlan = Vlan.objects.get(net_ident='employeevlan')

        swpvlan = l2trace.get_vlan_downlink_to_netbox(foo_sw1, employee_vlan)
        assert swpvlan is not None
        assert swpvlan.vlan.vlan == 20
        assert swpvlan.interface.ifname == 'Gi0/13'
        assert swpvlan.interface.netbox == foo_gw


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestUplink:
    def test_foo_sw1_vlan_uplink_should_be_gi_0_1(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')

        swpvlan = l2trace.get_vlan_uplink_from_netbox(foo_sw1)
        assert swpvlan is not None
        assert swpvlan.vlan.vlan == 10
        assert swpvlan.interface.ifname == 'Gi0/1'

    def test_foo_sw1_employee_vlan_uplink_should_be_gi_0_1(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        employee_vlan = Vlan.objects.get(net_ident='employeevlan')

        swpvlan = l2trace.get_vlan_uplink_from_netbox(foo_sw1, employee_vlan)
        assert swpvlan is not None
        assert swpvlan.vlan == employee_vlan
        assert swpvlan.interface.ifname == 'Gi0/1'


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestHost:
    def test_host_without_resolvable_name(self, l2trace_topology):
        ip = '10.99.99.99'
        h = l2trace.Host(ip)
        assert h.host == ip
        assert h.ip == ip
        assert h.hostname == ip

    def test_hosts_are_equal(self, l2trace_topology):
        host1 = l2trace.Host('10.99.99.99')
        host2 = l2trace.Host('10.99.99.99')
        assert host1 == host2

    def test_host_with_host_argument_returns_equal_instance(self, l2trace_topology):
        host1 = l2trace.Host('10.99.99.99')
        host2 = l2trace.Host(host1)
        assert host1 == host2


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestStartPath:
    def test_start_path_for_foo_sw1_ip_should_be_on_vlan_10(self, l2trace_topology):
        node = l2trace.get_start_path('10.0.0.11')
        assert node is not None
        assert node.vlan.vlan == 10
        assert node.if_in is None
        assert isinstance(node.host, Netbox)
        assert node.host.sysname == 'foo-sw1.example.org'

    def test_start_path_for_employee1_should_be_on_vlan_20(self, l2trace_topology):
        ip = '10.0.20.10'
        node = l2trace.get_start_path(ip)
        assert node is not None
        assert node.vlan.vlan == 20
        assert node.if_in is None
        assert isinstance(node.host, l2trace.Host)
        assert node.host.hostname == ip
        assert node.if_out is None


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestPath:
    def test_path_for_foo_sw1_should_be_2_long(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        path = l2trace.get_path(foo_sw1.ip)
        assert len(path) == 2

    def test_path_for_foo_sw1_should_start_with_foo_sw1(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        path = l2trace.get_path(foo_sw1.ip)
        assert path[0].host == foo_sw1

    def test_path_for_foo_sw1_should_end_at_foo_gw(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        path = l2trace.get_path(foo_sw1.ip)
        assert path[-1].host == foo_gw

    def test_path_for_foo_sw1_should_be_on_vlan_10(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        path = l2trace.get_path(foo_sw1.ip)
        assert path[0].vlan.vlan == 10
        assert path[1].vlan.vlan == 10

    def test_path_for_employee1_should_be_3_long(self, l2trace_topology):
        path = l2trace.get_path('10.0.20.10')
        assert len(path) == 3

    def test_path_for_employee2_should_be_3_long(self, l2trace_topology):
        path = l2trace.get_path('10.0.20.90')
        assert len(path) == 3, path

    def test_path_for_employee1_should_be_on_vlan_20(self, l2trace_topology):
        path = l2trace.get_path('10.0.20.10')
        assert path[0].vlan.vlan == 20
        assert path[1].vlan.vlan == 20

    def test_path_for_employee1_should_start_with_employee_1(self, l2trace_topology):
        path = l2trace.get_path('10.0.20.10')
        assert isinstance(path[0].host, l2trace.Host)

    def test_path_for_employee1_should_end_with_foo_gw(self, l2trace_topology):
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        path = l2trace.get_path('10.0.20.10')
        assert path[-1].host == foo_gw


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestTrace:
    def test_make_rows_returns_generator(self, l2trace_topology):
        tracequery = l2trace.L2TraceQuery('10.0.20.10', '')
        tracequery.trace()
        assert isinstance(tracequery.make_rows(), types.GeneratorType)

    def test_make_rows_generates_result_rows(self, l2trace_topology):
        tracequery = l2trace.L2TraceQuery('10.0.20.10', '')
        tracequery.trace()
        generator = tracequery.make_rows()
        first = next(generator)
        assert isinstance(first, l2trace.ResultRow)

    def test_first_row_is_host_from(self, l2trace_topology):
        ip = '10.0.20.10'
        tracequery = l2trace.L2TraceQuery(ip, '')
        tracequery.trace()
        first_row = next(tracequery.make_rows())
        assert first_row.sysname == ip

    def test_first_and_last_rows_match_hosts(self, l2trace_topology):
        ip1 = '10.0.20.10'
        ip2 = '10.0.20.90'
        tracequery = l2trace.L2TraceQuery(ip1, ip2)
        tracequery.trace()
        rows = list(tracequery.make_rows())
        assert rows[0].sysname == ip1, tracequery.path
        assert rows[-1].sysname == ip2, tracequery.path

    def test_employee_path_passes_through_foo_sw1(self, l2trace_topology):
        ip1 = '10.0.20.10'
        ip2 = '10.0.20.90'
        tracequery = l2trace.L2TraceQuery(ip1, ip2)
        tracequery.trace()
        rows = list(tracequery.make_rows())
        assert len(rows) == 3, rows
        switch_row = rows[1]
        assert switch_row.sysname == 'foo-sw1.example.org'

    def test_should_not_fail_on_invalid_hosts(self, l2trace_topology):
        tracequery = l2trace.L2TraceQuery('s;dfl', "923urfk';")
        tracequery.trace()
        list(tracequery.make_rows())


@patch('nav.web.l2trace.Host.get_host_by_name', new=Mock(return_value=None))
@patch('nav.web.l2trace.Host.get_host_by_addr', new=Mock(return_value=None))
class TestJunction:
    def test_find_junction_should_return_same_host(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        from_path, to_path = self._make_paths(foo_sw1, foo_gw)
        (node1, node2) = l2trace.find_junction(from_path, to_path)
        assert node1.host == node2.host

    def test_find_junction_should_return_foo_sw1(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        from_path, to_path = self._make_paths(foo_sw1, foo_gw)
        (node1, node2) = l2trace.find_junction(from_path, to_path)
        assert node1.host == foo_sw1
        assert node2.host == foo_sw1

    def test_find_junction_should_return_nodes_from_paths(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        from_path, to_path = self._make_paths(foo_sw1, foo_gw)
        (from_node, to_node) = l2trace.find_junction(from_path, to_path)
        assert from_node in from_path
        assert to_node in to_path

    def test_join_at_junction_should_be_3_long(self, l2trace_topology):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        from_path, to_path = self._make_paths(foo_sw1, foo_gw)
        new_path = l2trace.join_at_junction(from_path, to_path)
        assert len(new_path) == 3, new_path

    def test_joined_path_should_start_and_end_with_correct_hosts(
        self, l2trace_topology
    ):
        foo_sw1 = Netbox.objects.get(sysname='foo-sw1.example.org')
        foo_gw = Netbox.objects.get(sysname='foo-gw.example.org')
        from_path, to_path = self._make_paths(foo_sw1, foo_gw)
        new_path = l2trace.join_at_junction(from_path, to_path)
        assert new_path[0] == from_path[0]
        assert new_path[-1] == to_path[-1]

    @staticmethod
    def _make_paths(foo_sw1, foo_gw):
        """Helper to create test paths for junction tests."""
        Host = l2trace.Host
        from_path = [
            l2trace.PathNode(None, None, Host('10.0.20.10'), None),
            l2trace.PathNode(None, None, foo_sw1, None),
            l2trace.PathNode(None, None, foo_gw, None),
        ]
        to_path = [
            l2trace.PathNode(None, None, foo_gw, None),
            l2trace.PathNode(None, None, foo_sw1, None),
            l2trace.PathNode(None, None, Host('10.0.20.90'), None),
        ]
        return from_path, to_path


###
#
# Fixtures
#
###


@pytest.fixture
def l2trace_topology(db):
    """Creates a complete network topology for l2trace testing.

    Topology:
    - foo-gw (router/GSW) at 10.0.0.1
      - Interfaces: Vl10, Vl20, Vl30, Gi0/13 (trunk to foo-sw1)
    - foo-sw1 (switch/SW) at 10.0.0.11
      - Interfaces: Gi0/1 (trunk to foo-gw), Gi0/10, Gi0/11, Gi0/12

    VLANs:
    - scope: 10.0.0.0/8
    - adminvlan (vlan 10): 10.0.0.0/24
    - employeevlan (vlan 20): 10.0.20.0/24
    - studentvlan (vlan 30): 10.0.30.0/24
    """
    # Create location, room, organization (use get_or_create to avoid conflicts)
    location, _ = Location.objects.get_or_create(id='somewhere')
    room, _ = Room.objects.get_or_create(id='testroom', defaults={'location': location})
    org, _ = Organization.objects.get_or_create(id='testorg')

    # Create netboxes
    foo_gw = Netbox(
        ip='10.0.0.1',
        sysname='foo-gw.example.org',
        room=room,
        organization=org,
        category_id='GSW',
        up='y',
        up_since=datetime(2010, 10, 6, 11, 40, 36),
    )
    foo_gw.save()

    foo_sw1 = Netbox(
        ip='10.0.0.11',
        sysname='foo-sw1.example.org',
        room=room,
        organization=org,
        category_id='SW',
        up='y',
        up_since=datetime(2010, 10, 6, 11, 40, 36),
    )
    foo_sw1.save()

    # Create VLANs
    scope_vlan = Vlan(net_type_id='scope', net_ident='l2trace_scope')
    scope_vlan.save()

    admin_vlan = Vlan(vlan=10, net_type_id='lan', net_ident='adminvlan')
    admin_vlan.save()

    employee_vlan = Vlan(vlan=20, net_type_id='lan', net_ident='employeevlan')
    employee_vlan.save()

    student_vlan = Vlan(vlan=30, net_type_id='lan', net_ident='studentvlan')
    student_vlan.save()

    # Create prefixes (use get_or_create for scope prefix which may exist)
    scope_prefix, _ = Prefix.objects.get_or_create(
        net_address='10.0.0.0/8', defaults={'vlan': scope_vlan}
    )

    admin_prefix = Prefix(net_address='10.0.0.0/24', vlan=admin_vlan)
    admin_prefix.save()

    employee_prefix = Prefix(net_address='10.0.20.0/24', vlan=employee_vlan)
    employee_prefix.save()

    student_prefix = Prefix(net_address='10.0.30.0/24', vlan=student_vlan)
    student_prefix.save()

    # Create interfaces on foo-sw1
    sw1_gi01 = Interface(
        netbox=foo_sw1,
        ifindex=1,
        ifname='Gi0/1',
        ifalias='o: foo-gw',
        vlan=1,
        trunk=True,
        to_netbox=foo_gw,
    )
    sw1_gi01.save()

    sw1_gi010 = Interface(
        netbox=foo_sw1,
        ifindex=10,
        ifname='Gi0/10',
        ifalias='Employee 1',
        vlan=20,
        trunk=False,
    )
    sw1_gi010.save()

    sw1_gi011 = Interface(
        netbox=foo_sw1,
        ifindex=11,
        ifname='Gi0/11',
        ifalias='Employee 2',
        vlan=20,
        trunk=False,
    )
    sw1_gi011.save()

    sw1_gi012 = Interface(
        netbox=foo_sw1,
        ifindex=12,
        ifname='Gi0/12',
        ifalias='Student 13',
        vlan=30,
        trunk=False,
    )
    sw1_gi012.save()

    # Create interfaces on foo-gw
    gw_vl10 = Interface(
        netbox=foo_gw,
        ifindex=10,
        ifname='Vl10',
        trunk=False,
    )
    gw_vl10.save()

    gw_vl20 = Interface(
        netbox=foo_gw,
        ifindex=20,
        ifname='Vl20',
        trunk=False,
    )
    gw_vl20.save()

    gw_vl30 = Interface(
        netbox=foo_gw,
        ifindex=30,
        ifname='Vl30',
        trunk=False,
    )
    gw_vl30.save()

    gw_gi013 = Interface(
        netbox=foo_gw,
        ifindex=13,
        ifname='Gi0/13',
        ifalias='d: switch1',
        vlan=1,
        trunk=True,
        to_netbox=foo_sw1,
    )
    gw_gi013.save()

    # Create SwPortVlan entries (switch port to vlan mappings)
    SwPortVlan(interface=sw1_gi010, vlan=employee_vlan, direction='n').save()
    SwPortVlan(interface=gw_gi013, vlan=admin_vlan, direction='n').save()
    SwPortVlan(interface=gw_gi013, vlan=employee_vlan, direction='n').save()
    SwPortVlan(interface=sw1_gi01, vlan=admin_vlan, direction='o').save()
    SwPortVlan(interface=sw1_gi01, vlan=employee_vlan, direction='o').save()
    SwPortVlan(interface=sw1_gi011, vlan=employee_vlan, direction='n').save()
    SwPortVlan(interface=gw_gi013, vlan=student_vlan, direction='n').save()
    SwPortVlan(interface=sw1_gi01, vlan=student_vlan, direction='o').save()
    SwPortVlan(interface=sw1_gi012, vlan=student_vlan, direction='d').save()

    # Create GwPortPrefix entries (router interface to prefix mappings)
    GwPortPrefix(
        interface=gw_vl10, prefix=admin_prefix, gw_ip='10.0.1.1', virtual=False
    ).save()
    GwPortPrefix(
        interface=gw_vl20, prefix=employee_prefix, gw_ip='10.0.20.1', virtual=False
    ).save()
    GwPortPrefix(
        interface=gw_vl20, prefix=student_prefix, gw_ip='10.0.30.1', virtual=False
    ).save()

    # Create ARP entries
    Arp(
        netbox=foo_gw,
        sysname='foo-gw.example.org',
        ip='10.0.20.10',
        mac='00:01:02:03:04:05',
        start_time=datetime(2010, 10, 6, 11, 40, 36),
        end_time=datetime(9999, 12, 31, 23, 59, 59, 999999),
    ).save()

    Arp(
        netbox=foo_gw,
        sysname='foo-gw.example.org',
        ip='10.0.20.90',
        mac='00:01:02:03:04:90',
        start_time=datetime(2010, 10, 6, 10, 13, 20),
        end_time=datetime(9999, 12, 31, 23, 59, 59, 999999),
    ).save()

    Arp(
        netbox=foo_gw,
        sysname='foo-gw.example.org',
        ip='10.0.30.13',
        mac='00:01:02:03:04:13',
        start_time=datetime(2010, 10, 6, 9, 13, 20),
        end_time=datetime(9999, 12, 31, 23, 59, 59, 999999),
    ).save()

    # Create CAM entries
    Cam(
        netbox=foo_sw1,
        sysname='foo-sw1.example.org',
        ifindex=10,
        module='',
        port='Gi0/10',
        mac='00:01:02:03:04:05',
        start_time=datetime(2010, 10, 6, 11, 40, 36),
        end_time=datetime(9999, 12, 31, 23, 59, 59, 999999),
    ).save()

    Cam(
        netbox=foo_sw1,
        sysname='foo-sw1.example.org',
        ifindex=11,
        module='',
        port='Gi0/11',
        mac='00:01:02:03:04:90',
        start_time=datetime(2010, 10, 6, 10, 13, 0),
        end_time=datetime(9999, 12, 31, 23, 59, 59, 999999),
    ).save()

    Cam(
        netbox=foo_sw1,
        sysname='foo-sw1.example.org',
        ifindex=12,
        module='',
        port='Gi0/12',
        mac='00:01:02:03:04:13',
        start_time=datetime(2010, 10, 6, 9, 13, 20),
        end_time=datetime(9999, 12, 31, 23, 59, 59, 999999),
    ).save()

    yield {
        'foo_gw': foo_gw,
        'foo_sw1': foo_sw1,
        'admin_vlan': admin_vlan,
        'employee_vlan': employee_vlan,
        'student_vlan': student_vlan,
    }

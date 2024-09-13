from unittest import TestCase
from nav.ipdevpoll.storage import ContainerRepository
from nav.ipdevpoll.shadows import Vlan, Prefix, Netbox, Interface
from mock import patch, Mock


class MixedNetTypeTest(TestCase):
    """Tests for guesstimation of net_type on Vlan's with mixed prefixes"""

    def setUp(self):
        repo = ContainerRepository()
        netbox = repo.factory(None, Netbox)
        netbox.id = 1
        vlan = repo.factory('20', Vlan)

        for addr in ('2001:700:1::/64', '10.0.1.0/30', 'fe80::/64'):
            prefix = repo.factory(addr, Prefix)
            prefix.vlan = vlan
            prefix.net_address = addr

        self.vlan = vlan
        self.repo = repo

    def test_link_net_with_big_ipv6_addr(self):
        with patch.multiple(
            self.vlan,
            _get_router_count_for_prefix=Mock(return_value=2),
            _get_virtual_address_count=Mock(return_value=0),
        ):
            net_type = self.vlan._guesstimate_net_type(self.repo)
            self.assertTrue(net_type is not None)
            self.assertEqual("link", net_type.id)

    def test_elink_net_with_big_ipv6_addr(self):
        with patch.multiple(
            self.vlan,
            _get_router_count_for_prefix=Mock(return_value=1),
            _get_virtual_address_count=Mock(return_value=0),
        ):
            net_type = self.vlan._guesstimate_net_type(self.repo)
            self.assertTrue(net_type is not None)
            self.assertEqual("elink", net_type.id)


class RFC3021NetTypeTest(TestCase):
    """RFC3021 Tests for guesstimation of net_type on Vlan's"""

    def setUp(self):
        repo = ContainerRepository()
        netbox = repo.factory(None, Netbox)
        netbox.id = 1
        vlan = repo.factory('42', Vlan)
        self.shadow_prefixes = []
        for addr in ('2001:700:1::/64', '10.0.42.0/31'):
            prefix = repo.factory(addr, Prefix)
            prefix.vlan = vlan
            prefix.net_address = addr
            self.shadow_prefixes.append(prefix)

        self.vlan = vlan
        self.repo = repo

    def test_elink_net_with_subnet_31_rfc3021_router_count_as_1(self):
        with patch.multiple(
            self.vlan,
            _get_router_count_for_prefix=Mock(return_value=1),
            _get_virtual_address_count=Mock(return_value=0),
        ):
            net_type = self.vlan._guesstimate_net_type(self.repo)
            self.assertEqual("elink", net_type.id)

    def test_link_net_with_subnet_31_rfc3021_router_count_as_2(self):
        with patch.multiple(
            self.vlan,
            _get_router_count_for_prefix=Mock(return_value=2),
            _get_virtual_address_count=Mock(return_value=0),
        ):
            net_type = self.vlan._guesstimate_net_type(self.repo)
            self.assertEqual('link', net_type.id)


class TestInterfaces(object):
    def test_strip_null_bytes_should_leave_normal_strings_unchanged(self):
        ifc = Interface()
        ifc.ifname = ifc.ifalias = ifc.ifdescr = "Foobar"
        ifc._strip_null_bytes(None)
        assert ifc.ifname == ifc.ifalias == ifc.ifdescr == "Foobar"

    def test_strip_null_bytes_should_strip_nullbytes(self):
        ifc = Interface()
        ifc.ifname = ifc.ifalias = ifc.ifdescr = "Foobar\x00"
        ifc._strip_null_bytes(None)
        assert ifc.ifname == ifc.ifalias == ifc.ifdescr == "Foobar"

    def test_strip_null_bytes_should_ignore_nonstrings(self):
        ifc = Interface()
        ifc.ifname = ifc.ifalias = ifc.ifdescr = 42
        ifc._strip_null_bytes(None)
        assert ifc.ifname == ifc.ifalias == ifc.ifdescr == 42

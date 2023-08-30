from mock import Mock

import pytest

from nav.oids import OID
from nav.enterprise.ids import VENDOR_ID_HEWLETT_PACKARD, VENDOR_ID_CISCOSYSTEMS
from nav.portadmin.management import ManagementFactory
from nav.portadmin.snmp.hp import HP
from nav.portadmin.snmp.cisco import Cisco


class TestPortadminManagementFactory:
    def test_get_hp(self, netbox_hp):
        handler = ManagementFactory.get_instance(netbox_hp)
        assert handler is not None, "Could not get handler-object"
        assert isinstance(handler, HP), "Wrong handler-type"

    def test_get_cisco(self, netbox_cisco):
        handler = ManagementFactory.get_instance(netbox_cisco)
        assert handler is not None, "Could not get handler-object"
        assert isinstance(handler, Cisco), "Wrong handler-type"


class TestPortadminResponseHP:
    def test_get_vlan_hp(self, handler_hp):
        # get hold of the read-only Snmp-object
        snmp_read_only_handler = handler_hp._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a vlan-number
        snmp_read_only_handler.get = Mock(return_value=666)
        ifc = Mock(baseport=1)
        assert handler_hp.get_interface_native_vlan(ifc) == 666, "getVlan-test failed"
        snmp_read_only_handler.get.assert_called_with(
            OID('.1.3.6.1.2.1.17.7.1.4.5.1.1.1')
        )

    def test_get_ifaliases_hp(self, handler_hp):
        # get hold of the read-only Snmp-object
        snmp_read_only_handler = handler_hp._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        walkdata = [('.1', b'hjalmar'), ('.2', b'snorre'), ('.3', b'bjarne')]
        expected = {1: 'hjalmar', 2: 'snorre', 3: 'bjarne'}
        snmp_read_only_handler.bulkwalk = Mock(return_value=walkdata)
        assert handler_hp._get_all_ifaliases() == expected, "getAllIfAlias failed."

    def test_set_ifalias_hp(self, handler_hp):
        # get hold of the read-write Snmp-object
        snmp_read_only_handler = handler_hp._get_read_write_handle()
        # replace set-method on Snmp-object with a mock-method
        # all set-methods return None
        snmp_read_only_handler.set = Mock(return_value=None)
        interface = Mock()
        interface.ifindex = 1
        assert (
            handler_hp.set_interface_description(interface, "punkt1") is None
        ), "setIfAlias failed"


class TestPortadminResponseCisco:
    def test_get_vlan_cisco(self, handler_cisco):
        # get hold of the read-only Snmp-object
        snmp_read_only_handler = handler_cisco._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a vlan-number
        snmp_read_only_handler.get = Mock(return_value=77)
        ifc = Mock(ifindex=1)
        assert handler_cisco.get_interface_native_vlan(ifc) == 77, "getVlan-test failed"
        snmp_read_only_handler.get.assert_called_with('1.3.6.1.4.1.9.9.68.1.2.2.1.2.1')

    def test_get_ifaliases_cisco(self, handler_cisco):
        # get hold of the read-only Snmp-object
        snmp_read_only_handler = handler_cisco._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        walkdata = [('.1', b'jomar'), ('.2', b'knut'), ('.3', b'hjallis')]
        expected = {1: 'jomar', 2: 'knut', 3: 'hjallis'}
        snmp_read_only_handler.bulkwalk = Mock(return_value=walkdata)
        assert handler_cisco._get_all_ifaliases() == expected, "getAllIfAlias failed."


@pytest.fixture
def profile():
    profile = Mock()
    profile.snmp_version = 2
    profile.snmp_community = "public"
    return profile


@pytest.fixture
def netbox_hp(profile):
    vendor = Mock()
    vendor.id = u'hp'

    netbox_type = Mock()
    netbox_type.vendor = vendor
    netbox_type.get_enterprise_id.return_value = VENDOR_ID_HEWLETT_PACKARD

    netbox = Mock()
    netbox.type = netbox_type
    netbox.ip = '10.240.160.39'
    netbox.get_preferred_snmp_management_profile.return_value = profile

    return netbox


@pytest.fixture
def netbox_cisco(profile):
    vendor = Mock()
    vendor.id = u'cisco'

    netbox_type = Mock()
    netbox_type.vendor = vendor
    netbox_type.get_enterprise_id.return_value = VENDOR_ID_CISCOSYSTEMS

    netbox = Mock()
    netbox.type = netbox_type
    netbox.ip = '10.240.160.38'
    netbox.get_preferred_snmp_management_profile.return_value = profile

    return netbox


@pytest.fixture
def handler_hp(netbox_hp):
    return ManagementFactory.get_instance(netbox_hp)


@pytest.fixture
def handler_cisco(netbox_cisco):
    return ManagementFactory.get_instance(netbox_cisco)

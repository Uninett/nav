"""Tests for Arnold using snmp objects"""
from nav.arnold import change_port_status, change_port_vlan
from mock import Mock, patch
import unittest

@patch('nav.Snmp.Snmp', autospec=True)
class TestArnoldSnmp(unittest.TestCase):
    """Testclass for Arnold"""

    def setUp(self):
        self.ip = '10.0.0.1'
        self.read_write = 'public'
        self.read_only = 'private'
        self.ifindex = 1
        self.port_status_oid = '.1.3.6.1.2.1.2.2.1.7'

        self.netbox = self.create_netbox_mock()
        self.interface = self.create_interface_mock()


    def create_interface_mock(self):
        """Create interface model mock object"""
        interface = Mock()
        interface.netbox = self.netbox
        interface.ifindex = self.ifindex
        return interface

    def create_netbox_mock(self):
        """Create netbox model mock object"""
        netbox = Mock()
        netbox.ip = self.ip
        netbox.read_write = self.read_write
        netbox.read_only = self.read_write
        netbox.snmp_version = 1
        netbox.type.vendor.id = 'cisco'
        return netbox

    def test_change_port_status_enable(self, snmp):
        """Test enabling of a port"""
        instance = snmp.return_value
        identity = Mock()
        identity.interface = self.interface
        change_port_status('enable', identity)

        snmp.assert_called_once_with(self.ip, self.read_write, version=1)
        instance.set.assert_called_once_with(
            self.port_status_oid + '.' + str(self.ifindex), 'i', 1)


    def test_change_port_status_disable(self, snmp):
        """Test disabling of a port"""
        instance = snmp.return_value
        identity = Mock()
        identity.interface = self.interface
        change_port_status('disable', identity)

        snmp.assert_called_once_with(self.ip, self.read_write, version=1)
        instance.set.assert_called_once_with(
            self.port_status_oid + '.' + str(self.ifindex), 'i', 2)


    def test_change_port_vlan_cisco(self, snmp):
        """Test changing of vlan on cisco equipment"""
        fromvlan = 23
        tovlan = 24

        ciscooid = "1.3.6.1.4.1.9.9.68.1.2.2.1.2"
        #hpoid = "1.3.6.1.2.1.17.7.1.4.5.1.1"

        instance = snmp.return_value
        instance.get.return_value = fromvlan

        identity = Mock()
        identity.interface = self.interface

        query = ciscooid + '.' + str(identity.interface.ifindex)
        self.assertEqual(change_port_vlan(identity, tovlan), fromvlan)
        instance.get.assert_called_once_with(query)
        instance.set.assert_called_once_with(query, 'i', tovlan)


    def test_change_port_vlan_hp(self, snmp):
        """Test changing of vlan on hp or other equipment"""
        fromvlan = 23
        tovlan = 24

        #ciscooid = "1.3.6.1.4.1.9.9.68.1.2.2.1.2"
        #hpoid = "1.3.6.1.2.1.17.7.1.4.5.1.1"

        instance = snmp.return_value
        instance.get.return_value = fromvlan

        identity = Mock()
        identity.interface = self.interface
        identity.interface.netbox.type.vendor.id = 'hp'

        with patch('nav.arnold.compute_octet_string'):
            self.assertEqual(change_port_vlan(identity, tovlan), fromvlan)

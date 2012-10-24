
from nav.arnold import change_port_status
from mock import Mock, patch
import unittest

@patch('nav.Snmp.Snmp', autospec=True)
class TestArnold(unittest.TestCase):
    """Testclass for Arnold"""

    def setUp(self):
        self.ip = '10.0.0.1'
        self.community = 'test'
        self.ifindex = 1
        self.port_status_oid = '.1.3.6.1.2.1.2.2.1.7'

        self.netbox = self.create_netbox_mock()
        self.interface = self.create_interface_mock()


    def create_interface_mock(self):
        interface = Mock()
        interface.netbox = self.netbox
        interface.ifindex = self.ifindex
        return interface

    def create_netbox_mock(self):
        netbox = Mock()
        netbox.ip = self.ip
        netbox.read_write = self.community
        netbox.snmp_version = 1
        return netbox

    def test_change_port_status_enable(self, snmp):
        instance = snmp.return_value
        identity = Mock()
        identity.interface = self.interface
        change_port_status('enable', identity)

        snmp.assert_called_once_with(self.ip, self.community, version=1)
        instance.set.assert_called_once_with(
            self.port_status_oid + '.' + str(self.ifindex), 'i', 1)


    def test_change_port_status_disable(self, snmp):
        instance = snmp.return_value
        identity = Mock()
        identity.interface = self.interface
        change_port_status('disable', identity)

        snmp.assert_called_once_with(self.ip, self.community, version=1)
        instance.set.assert_called_once_with(
            self.port_status_oid + '.' + str(self.ifindex), 'i', 2)

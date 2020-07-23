from mock import Mock

import unittest

from django.utils import six

from nav.oids import OID
from nav.enterprise.ids import VENDOR_ID_HEWLETT_PACKARD, VENDOR_ID_CISCOSYSTEMS
from nav.portadmin.management import *

###############################################################################
from nav.portadmin.vlan import FantasyVlan


class PortadminResponseTest(unittest.TestCase):
    def setUp(self):
        self.hpVendor = Mock()
        self.hpVendor.id = u'hp'

        self.ciscoVendor = Mock()
        self.ciscoVendor.id = u'cisco'

        self.hpType = Mock()
        self.hpType.vendor = self.hpVendor
        self.hpType.get_enterprise_id.return_value = VENDOR_ID_HEWLETT_PACKARD

        self.ciscoType = Mock()
        self.ciscoType.vendor = self.ciscoVendor
        self.ciscoType.get_enterprise_id.return_value = VENDOR_ID_CISCOSYSTEMS

        self.netboxHP = Mock()
        self.netboxHP.type = self.hpType
        self.netboxHP.ip = '10.240.160.39'
        self.netboxHP.snmp_version = "2c"

        self.netboxCisco = Mock()
        self.netboxCisco.type = self.ciscoType
        self.netboxCisco.ip = '10.240.160.38'
        self.netboxCisco.snmp_version = "2c"

        self.snmpReadOnlyHandler = None
        self.handler = None

    def tearDown(self):
        self.hpVendor = None
        self.ciscoVendor = None
        self.hpType = None
        self.ciscoType = None
        self.netboxHP = None
        self.netboxCisco = None
        self.handler = None
        self.snmpReadOnlyHandler = None
        self.snmpReadWriteHandler = None

    ####################################################################
    #  HP-netbox

    def test_management_factory_get_hp(self):
        self.handler = ManagementFactory.get_instance(self.netboxHP)
        self.assertNotEqual(self.handler, None,
                            'Could not get handler-object')
        self.assertIsInstance(self.handler, HP, msg='Wrong handler-type')

    def test_get_vlan_hp(self):
        self.handler = ManagementFactory.get_instance(self.netboxHP)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a vlan-number
        self.snmpReadOnlyHandler.get = Mock(return_value=666)
        ifc = Mock(baseport=1)
        self.assertEqual(self.handler.get_interface_native_vlan(ifc), 666,
                                "getVlan-test failed")
        self.snmpReadOnlyHandler.get.assert_called_with(
            OID('.1.3.6.1.2.1.17.7.1.4.5.1.1.1')
        )

    def test_get_ifaliases_hp(self):
        self.handler = ManagementFactory.get_instance(self.netboxHP)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        walkdata = [('.1', b'hjalmar'), ('.2', b'snorre'), ('.3', b'bjarne')]
        expected = {1: 'hjalmar', 2: 'snorre', 3: 'bjarne'}
        self.snmpReadOnlyHandler.bulkwalk = Mock(return_value=walkdata)
        self.assertEqual(self.handler._get_all_ifaliases(),
                         expected,
                         "getAllIfAlias failed.")

    def test_set_ifalias_hp(self):
        self.handler = ManagementFactory.get_instance(self.netboxHP)
        # get hold of the read-write Snmp-object
        self.snmpReadWriteHandler = self.handler._get_read_write_handle()

        # replace set-method on Snmp-object with a mock-method
        # all set-methods return None
        self.snmpReadWriteHandler.set = Mock(return_value=None)
        interface = Mock()
        interface.ifindex = 1
        self.assertEqual(
            self.handler.set_interface_description(interface, "punkt1"),
            None,
            "setIfAlias failed",
        )

    ####################################################################
    #  CISCO-netbox

    def test_management_factory_get_cisco(self):
        ####################################################################
        #  cisco-netbox
        self.handler = ManagementFactory.get_instance(self.netboxCisco)
        self.assertNotEqual(self.handler, None, 'Could not get handler-object')
        self.assertIsInstance(self.handler, Cisco, 'Wrong handler-type')

    def test_get_vlan_cisco(self):
        self.handler = ManagementFactory.get_instance(self.netboxCisco)
        assert type(self.handler) == Cisco
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a vlan-number
        self.snmpReadOnlyHandler.get = Mock(return_value=77)
        ifc = Mock(ifindex=1)
        self.assertEqual(self.handler.get_interface_native_vlan(ifc), 77,
                                "getVlan-test failed")
        self.snmpReadOnlyHandler.get.assert_called_with('1.3.6.1.4.1.9.9.68.1.2.2.1.2.1')

    def test_get_ifaliases_cisco(self):
        self.handler = ManagementFactory.get_instance(self.netboxCisco)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        walkdata = [('.1', b'jomar'), ('.2', b'knut'), ('.3', b'hjallis')]
        expected = {1: 'jomar', 2: 'knut', 3: 'hjallis'}
        self.snmpReadOnlyHandler.bulkwalk = Mock(return_value=walkdata)
        self.assertEqual(self.handler._get_all_ifaliases(),
                         expected, "getAllIfAlias failed.")


if __name__ == '__main__':
    unittest.main()

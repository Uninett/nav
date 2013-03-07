from mock import Mock

import unittest
from nav.models.manage import Netbox, Interface
from nav.web.portadmin.utils import *
from nav.portadmin.snmputils import *

###############################################################################

class PortadminResponseTest(unittest.TestCase):
    def setUp(self):
        self.hpVendor = Mock()
        self.hpVendor.id = u'hp'

        self.ciscoVendor = Mock()
        self.ciscoVendor.id  = u'cisco'
        
        self.hpType = Mock()
        self.hpType.vendor = self.hpVendor

        self.ciscoType = Mock()
        self.ciscoType.vendor = self.ciscoVendor

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

    def test_snmp_factory_get_hp(self):
        self.handler = SNMPFactory.get_instance(self.netboxHP)
        self.assertNotEqual(self.handler, None,
                                'Could not get handler-object')
        self.assertEquals(self.handler.__unicode__(),  u'hp',
                                'Wrong handler-type')
    
    def test_get_ifalias_hp(self):
        self.handler = SNMPFactory.get_instance(self.netboxHP)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a ifalias
        self.snmpReadOnlyHandler.get = Mock(return_value="pkt: 999") 
        self.assertEquals(self.handler.get_if_alias(1), "pkt: 999",
                                "getIfAlias-test failed")
        
    def test_get_vlan_hp(self):
        self.handler = SNMPFactory.get_instance(self.netboxHP)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a vlan-number
        self.snmpReadOnlyHandler.get = Mock(return_value=666)
        self.assertEqual(self.handler.get_vlan(1), 666,
                                "getVlan-test failed")

    def test_get_ifaliases_hp(self):
        self.handler = SNMPFactory.get_instance(self.netboxHP)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        self.snmpReadOnlyHandler.bulkwalk = Mock(return_value=['hjalmar', 'snorre', 'bjarne'])
        self.assertEqual(self.handler.get_all_if_alias(),
            ['hjalmar', 'snorre', 'bjarne'], "getAllIfAlias failed.")
        
    def test_set_ifalias_hp(self):
        self.handler = SNMPFactory.get_instance(self.netboxHP)
        # get hold of the read-write Snmp-object
        self.snmpReadWriteHandler = self.handler._get_read_write_handle()

        # replace set-method on Snmp-object with a mock-method
        # all set-methods return None
        self.snmpReadWriteHandler.set = Mock( return_value = None)
        self.assertEqual(self.handler.set_if_alias(1, 'punkt1'), None,
                            'setIfAlias failed')

    def test_get_vlans(self):
        handler = SNMPFactory.get_instance(self.netboxHP)

        interface = Mock()
        swportvlan1 = Mock(vlan=Mock(vlan=1))
        swportvlan2 = Mock(vlan=Mock(vlan=2))

        interface.swportvlan_set.all.return_value = [swportvlan1, swportvlan2]

        self.assertEqual(sorted(handler._find_vlans_for_interface(interface)),
                         [FantasyVlan(1), FantasyVlan(2)])

    ####################################################################
    #  CISCO-netbox

    def test_snmp_factory_get_cisco(self):
        ####################################################################
        #  cisco-netbox
        self.handler = SNMPFactory.get_instance(self.netboxCisco)
        self.assertNotEqual(self.handler, None, 'Could not get handler-object')
        self.assertEquals(self.handler.__unicode__(),  u'cisco', 'Wrong handler-type')
    def test_get_ifaliases_cisco(self):
        self.handler = SNMPFactory.get_instance(self.netboxCisco)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a ifalias
        self.snmpReadOnlyHandler.get = Mock(return_value="pkt: 88")
        self.assertEquals(self.handler.get_if_alias(1), "pkt: 88",
                                "getIfAlias-test failed")

    def test_get_vlan_cisco(self):
        self.handler = SNMPFactory.get_instance(self.netboxCisco)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # this get-method returns a vlan-number
        self.snmpReadOnlyHandler.get = Mock(return_value=77)
        self.assertEqual(self.handler.get_vlan(1), 77,
                                "getVlan-test failed")

    def test_get_ifaliases_cisco(self):
        self.handler = SNMPFactory.get_instance(self.netboxCisco)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        self.snmpReadOnlyHandler.bulkwalk = Mock(return_value=['jomar', 'knut', 'hjallis'])
        self.assertEqual(self.handler.get_all_if_alias(),
            ['jomar', 'knut', 'hjallis'], "getAllIfAlias failed.")


if __name__ == '__main__':
    unittest.main()

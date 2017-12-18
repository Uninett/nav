from mock import Mock

import unittest

from django.utils import six

from nav.models.manage import Interface
from nav.web.portadmin.utils import *
from nav.portadmin.snmputils import *

###############################################################################


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

        profile = Mock()
        profile.snmp_version = 2

        self.netboxHP = Mock()
        self.netboxHP.type = self.hpType
        self.netboxHP.ip = '10.240.160.39'
        self.netboxHP.readonly_connection_profile = profile
        self.netboxHP.readwrite_connection_profile = profile

        self.netboxCisco = Mock()
        self.netboxCisco.type = self.ciscoType
        self.netboxCisco.ip = '10.240.160.38'
        self.netboxCisco.readonly_connection_profile = profile
        self.netboxCisco.readwrite_connection_profile = profile

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
        self.assertEqual(six.text_type(self.handler),  u'hp',
                          'Wrong handler-type')

    def test_get_ifaliases_hp(self):
        self.handler = SNMPFactory.get_instance(self.netboxHP)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        self.snmpReadOnlyHandler.bulkwalk = Mock(return_value=['hjalmar', 'snorre', 'bjarne'])
        self.assertEqual(self.handler._get_all_if_alias(),
                         ['hjalmar', 'snorre', 'bjarne'],
                         "getAllIfAlias failed.")

    def test_set_ifalias_hp(self):
        self.handler = SNMPFactory.get_instance(self.netboxHP)
        # get hold of the read-write Snmp-object
        self.snmpReadWriteHandler = self.handler._get_read_write_handle()

        # replace set-method on Snmp-object with a mock-method
        # all set-methods return None
        self.snmpReadWriteHandler.set = Mock(return_value=None)
        ifc = Interface(ifindex=1)
        self.assertEqual(self.handler.set_if_alias(ifc, 'punkt1'), None,
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
        self.handler = SNMPFactory.get_instance(self.netboxCisco)
        self.assertNotEqual(self.handler, None, 'Could not get handler-object')
        self.assertEqual(six.text_type(self.handler),  u'cisco', 'Wrong handler-type')
        self.assertEqual(type(self.handler), Cisco, 'Wrong handler-type')

    def test_get_ifaliases_cisco(self):
        self.handler = SNMPFactory.get_instance(self.netboxCisco)
        # get hold of the read-only Snmp-object
        self.snmpReadOnlyHandler = self.handler._get_read_only_handle()
        # replace get-method on Snmp-object with a mock-method
        # for getting all IfAlias
        self.snmpReadOnlyHandler.bulkwalk = Mock(return_value=['jomar', 'knut', 'hjallis'])
        self.assertEqual(self.handler._get_all_if_alias(),
                         ['jomar', 'knut', 'hjallis'], "getAllIfAlias failed.")


if __name__ == '__main__':
    unittest.main()

#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Unit tests for the nav.mcc.interfaces."""

from nav.mcc.interfaces import *
from nav.mcc.utils import RRDcontainer, Datasource
from mock import Mock, patch
import unittest

class InterfaceTest(unittest.TestCase):

    def setUp(self):
        self.datasources = {'1': ['ifInOctets',
                                  'ifOutOctets',
                                  'ifInErrors',
                                  'ifOutErrors',
                                  'ifInUcastPkts',
                                  'ifOutUcastPkts'],
                            '2c': ['ifHCInOctets',
                                   'ifHCOutOctets',
                                   'ifInErrors',
                                   'ifOutErrors',
                                   'ifInUcastPkts',
                                   'ifOutUcastPkts']}
        self.datasource_units = {'ifHCInOctets': 'bytes/s',
                                 'ifHCOutOctets': 'bytes/s',
                                 'ifInErrors': 'packets',
                                 'ifOutErrors': 'packets',
                                 'ifInUcastPkts': 'packets',
                                 'ifOutUcastPkts': 'packets'}


    def test_format_snmp_version_v1(self):
        router = Mock()
        router.snmp_version = 2
        self.assertEqual(format_snmp_version(router), '2c')
        router.snmp_version = 1

    def test_format_snmp_version_v2(self):
        router = Mock()
        router.snmp_version = 1
        self.assertEqual(format_snmp_version(router), '1')

    def test_interface_datasources(self):
        mockdata = """
            targetType  standard-interface
                    ds      =       "ifInOctets, ifOutOctets, ifInErrors,ifOutErrors, ifInUcastPkts, ifOutUcastPkts"
                    view    =       "Octets: ifInOctets ifOutOctets, UcastPackets: ifInUcastPkts ifOutUcastPkts, Errors: ifInErrors ifOutErrors"

            targetType  sub-interface
                    ds      =       "ifInOctets, ifOutOctets"
                    view    =       "Octets: ifInOctets ifOutOctets"

            targetType  subv2-interface
                    ds      =       "ifHCInOctets, ifHCOutOctets"
                    view    =       "Octets: ifHCInOctets ifHCOutOctets"

            targetType  snmpv2-interface
                    ds      =       "ifHCInOctets, ifHCOutOctets, ifInErrors,ifOutErrors, ifInUcastPkts, ifOutUcastPkts"
                    view    =       "Octets: ifHCInOctets ifHCOutOctets, UcastPackets: ifInUcastPkts ifOutUcastPkts, Errors: ifInErrors ifOutErrors"
        """

        with patch("nav.mcc.interfaces.read_defaults_file",
                   return_value=mockdata.split('\n')):

            datasources = get_interface_datasources("blapp")
            self.assertEqual(datasources, self.datasources)


    def test_create_rrd_container(self):
        interface = Mock()
        netbox = Mock()
        netbox.sysname = 'uninett-gw'
        netbox.id = 1
        netbox.snmp_version = 2

        interface.netbox = netbox
        interface.id = 2
        interface.speed = 200

        targetname = 'blapp'
        module = 'switch-port-counters'

        dummycontainer = RRDcontainer('blapp.rrd', 1, 'uninett-gw',
                                      'interface', 2, speed=200,
                                      category='switch-port-counters')
        for index, datasource in enumerate(self.datasources['2c']):
            dummycontainer.datasources.append(
                Datasource('ds' + str(index), datasource, 'DERIVE',
                           self.datasource_units[datasource]))

        container = create_rrd_container(self.datasources, interface,
                                         targetname, module)
        self.assertEqual(container.datasources, dummycontainer.datasources)
        self.assertEqual(container, dummycontainer)


    def test_create_all_target(self):
        dummy = """target "all"\n\ttargets = "1;2"\n\torder = 3\n"""

        self.assertEqual("".join(create_all_target(["1","2"], 2)), dummy)

    def test_create_target(self):
        interface = Mock()
        interface.ifalias = "test"
        interface.ifname = "ifname"
        interface.ifindex = 3
        targetname = "blapp"
        reversecounter = 10

        dummy = """target "blapp"\n\tdisplay-name = "ifname"\n\tinterface-index = 3\n\tshort-desc = "test"\n\tifname = "ifname"\n\torder = 10\n\n"""
        result = "".join(create_target(interface, targetname, reversecounter))
        self.assertEqual(result, dummy)

    def test_create_default_target_snmpv1(self):
        netbox = Mock()
        netbox.ip = "129.241.23.49"
        netbox.read_only = "public"
        snmp_version = "1"
        module = "blapp"

        dummy = """target --default--\n\tsnmp-host\t= 129.241.23.49\n\tsnmp-version\t= 1\n\tsnmp-community\t= public\n\n"""
        result = "".join(create_default_target(netbox, snmp_version, module))

        self.assertEqual(result, dummy)

    def test_create_default_target_snmpv2(self):
        netbox = Mock()
        netbox.ip = "129.241.23.49"
        netbox.read_only = "public"
        snmp_version = "2c"
        module = "blapp"

        dummy = """target --default--\n\tsnmp-host\t= 129.241.23.49\n\tsnmp-version\t= 2c\n\ttarget-type\t= snmpv2-interface\n\tsnmp-community\t= public\n\n"""
        result = "".join(create_default_target(netbox, snmp_version, module))

        self.assertEqual(result, dummy)

    def test_create_default_target_ipv6(self):
        netbox = Mock()
        netbox.ip = "129.241.23.49"
        netbox.read_only = "public"
        snmp_version = "2c"
        module = "ipv6-counters"

        dummy = """target --default--\n\tsnmp-host\t= 129.241.23.49\n\tsnmp-version\t= 2c\n\ttarget-type\t= ipv6-interface\n\tsnmp-community\t= public\n\n"""
        result = "".join(create_default_target(netbox, snmp_version, module))

        self.assertEqual(result, dummy)

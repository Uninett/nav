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

from nav.mcc.interfaces import format_snmp_version, get_interface_datasources
from mock import Mock, patch
import unittest

class InterfaceTest(unittest.TestCase):

    def setUp(self):
        pass

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

        passdata = {'1': ['ifInOctets',
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

        with patch("nav.mcc.interfaces.read_defaults_file",
                   return_value=mockdata.split('\n')):

            datasources = get_interface_datasources("blapp")
            self.assertEqual(datasources, passdata)

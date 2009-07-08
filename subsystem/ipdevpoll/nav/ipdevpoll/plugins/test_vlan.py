# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import unittest

import os
os.environ['PYSNMP_API_VERSION'] = 'v3'
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'
from nav.ipdevpoll.plugins.vlan import Vlans

class VlansPluginTest(unittest.TestCase):

    def setUp(self):
        pass
    def testIfDescrParser_LAN(self):
        d = Vlans.parse_ifDescr('lan,math,staff')
        self.assertEqual(d['organisation'], 'math')
        self.assertEqual(d['usage'], 'staff')

        d = Vlans.parse_ifDescr('lan,physics,students,campus_dragv,340')
        self.assertEqual(d['organisation'], 'physics')
        self.assertEqual(d['usage'], 'students')
        self.assertEqual(d['comment'], 'campus_dragv')
        self.assertEqual(d['vlan'], '340')

        d = Vlans.parse_ifDescr('lan,math,staff2,campus_lade')
        self.assertEqual(d['organisation'], 'math')
        self.assertEqual(d['usage'], 'staff2')
        self.assertEqual(d['comment'], 'campus_lade')

        d = Vlans.parse_ifDescr('lan,foo')
        self.assertEquals(d, None)

    def testIfDescrParser_LINK(self):
        d = Vlans.parse_ifDescr('link,mts-gw')
        self.assertEqual(d['to_router'], 'mts-gw')

        d = Vlans.parse_ifDescr('link,moholt-gw,Tn_20022350,923')
        self.assertEqual(d['to_router'], 'moholt-gw')
        self.assertEqual(d['comment'], 'Tn_20022350')
        self.assertEqual(d['vlan'], '923')

    def testIfDescrParser_CORE(self):
        d = Vlans.parse_ifDescr('core,it,wlan')
        self.assertEqual(d['organisation'], 'it')
        self.assertEqual(d['usage'], 'wlan')

        d = Vlans.parse_ifDescr('core,it,fddi,manring,180')
        self.assertEqual(d['organisation'], 'it')
        self.assertEqual(d['usage'], 'fddi')
        self.assertEqual(d['comment'], 'manring')
        self.assertEqual(d['vlan'], '180')

        d = Vlans.parse_ifDescr('core,foo')
        self.assertEquals(d, None)

    def testIfDescrParser_ELINK(self):
        d = Vlans.parse_ifDescr('elink,trd-gw,uninett')
        self.assertEqual(d['to_router'], 'trd-gw')
        self.assertEqual(d['to_organisation'], 'uninett')

        d = Vlans.parse_ifDescr('elink,sintef-gw,sintef,,902')
        self.assertEqual(d['to_router'], 'sintef-gw')
        self.assertEqual(d['to_organisation'], 'sintef')
        self.assertEqual(d['vlan'], '902')

    def testIfDescrParser_INVALID(self):
        d = Vlans.parse_ifDescr('foobar,bar,baz')
        self.assertEquals(d, None)


if __name__ == '__main__':
        unittest.main()

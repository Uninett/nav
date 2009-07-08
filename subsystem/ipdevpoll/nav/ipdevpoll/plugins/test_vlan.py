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

    def testPortListParser(self):
        d = Vlans.vlan_port_list_parser('00 00 01 40 00 00 00 00')
        self.assertEquals(d, [24,26])

        d = Vlans.vlan_port_list_parser('00 00')
        self.assertEquals(d, [])

        d = Vlans.vlan_port_list_parser('')
        self.assertEquals(d, [])



if __name__ == '__main__':
        unittest.main()

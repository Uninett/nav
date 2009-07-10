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
from IPy import IP

os.environ['PYSNMP_API_VERSION'] = 'v3'
os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

from nav.models.manage import Prefix
from nav.ipdevpoll.utils import find_prefix

class ArpPluginTest(unittest.TestCase):
    def test_find_prefix(self):
        correct_ipv4 = IP('192.0.2.1')
        correct_ipv6 = IP('2001:db8:1234::1')

        loose_prefix = Prefix(
            net_address='2001:db8::/32'
        )
        tight_prefix = Prefix(
            net_address='2001:db8:1234::/48'
        )

        prefix1 = find_prefix(correct_ipv6, [loose_prefix, tight_prefix])
        prefix2 = find_prefix(correct_ipv6, [tight_prefix, loose_prefix])

        self.assertEqual(prefix1, tight_prefix)
        self.assertEqual(prefix2, tight_prefix)

        loose_prefix = Prefix(
            net_address='192.0.2/24'
        )
        tight_prefix = Prefix(
            net_address='192.0.2.0/26'
        )

        prefix1 = find_prefix(correct_ipv4, [loose_prefix, tight_prefix])
        prefix2 = find_prefix(correct_ipv4, [tight_prefix, loose_prefix])

        self.assertEqual(prefix1, tight_prefix)
        self.assertEqual(prefix2, tight_prefix)

if __name__ == '__main__':
    unittest.main()

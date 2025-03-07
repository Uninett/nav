#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Unittests for web/info/room"""

import unittest

from mock import Mock
from nav.models.manage import Netbox


class RoomViewsTest(unittest.TestCase):
    """Testclass for helper functions in roominfo's views module"""

    def setUp(self):
        """Test setup"""

        netbox1 = Netbox()
        netbox1.get_availability = Mock(
            return_value={'availability': {'day': None, 'month': 100.0, 'week': 100.0}}
        )
        netbox2 = Netbox()
        netbox2.get_availability = Mock(
            return_value={'availability': {'day': None, 'month': 100.0, 'week': None}}
        )
        self.netboxes = [netbox1, netbox2]

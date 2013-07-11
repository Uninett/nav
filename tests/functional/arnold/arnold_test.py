#
# Copyright (C) 2013 UNINETT AS
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
"""Selenium tests for arnold"""

import unittest
from .. import SeleniumTest, BASE_URL


class ArnoldTest(SeleniumTest):
    """Testrunner for Arnold selenium tests"""

    def setUp(self):
        super(ArnoldTest, self).setUp()
        self.url = BASE_URL + '/arnold'
        self.driver.get(self.url)

    def test_should_default_to_detained_ports(self):
        title = self.driver.title
        self.assertIn('Detentions', title)

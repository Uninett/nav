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
# pylint: disable=C0111, R0904
"""Selenium tests for arnold"""

from nav.tests.selenium import SeleniumTest


class ArnoldSeleniumTest(SeleniumTest):
    """Testrunner for the Arnold page"""

    def test_should_default_to_detained_ports(self):
        self.driver.get(self.get_url('arnold_index'))
        title = self.driver.title
        self.assertTrue('Detentions' in title)

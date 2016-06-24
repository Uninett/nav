#
# Copyright (C) 2015 UNINETT AS
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
"""Selenium tests for Status"""
from time import sleep

from nav.tests.selenium import LoggedInSeleniumTest

class StatusSeleniumTest(LoggedInSeleniumTest):
    """Testrunner for the Status page"""

    def setUp(self):
        """Setup"""
        super(StatusSeleniumTest, self).setUp()
        self.driver.get(self.get_url('/status/'))
        self.panel = self.driver.find_element_by_id('status-panel')
        self.filter_toggle = self.driver.find_element_by_class_name('toggle-panel')

    def test_panel_toggle(self):
        """Test if panel toggles when clicked"""
        initial_state = self.panel.is_displayed()
        self.filter_toggle.click()
        self.assertTrue(initial_state != self.panel.is_displayed(),
                        'Clicking filter_toggle did not do anything')

    def test_remember_last_panel_state(self):
        """Test if the panel stays in the same state after page refresh"""
        assert self.panel.is_displayed() == False
        self.filter_toggle.click()
        sleep(1)
        self.driver.refresh()
        # We need to fetch panel element again after a refresh
        self.panel = self.driver.find_element_by_id('status-panel')
        self.assertTrue(self.panel.is_displayed(),
                        'Panel did not stay in same state after page refresh')

#
# Copyright (C) 2015 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Selenium tests for simple searches on the navbar"""

from nav.tests.selenium import SeleniumTest


class NavBarSeleniumTest(SeleniumTest):
    """Testrunner for the Status page"""

    def setUp(self):
        """Setup"""
        super(NavBarSeleniumTest, self).setUp()
        self.driver.get(self.get_url('/'))
        self.query = self.driver.find_element_by_id('query')
        self.search_button = self.driver.find_element_by_css_selector(
                "input.button[type='submit']")

    def test_simple_ip_search(self):
        """Tests a search for an IP address"""
        ipaddr = "192.168.42.42"
        self.query.send_keys(ipaddr)
        self.search_button.click()
        caption = self.driver.find_element_by_tag_name('caption')
        self.assertIn(ipaddr, caption.text)

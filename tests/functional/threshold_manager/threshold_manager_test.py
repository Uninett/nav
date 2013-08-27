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
"""Tests for threshold manager"""

import os
from selenium.webdriver.support.select import Select, NoSuchElementException
from nav.tests.selenium import SeleniumTest


class ThresholdManagerSeleniumTest(SeleniumTest):
    """Test runner for threshold manager tests"""

    def setUp(self):
        super(ThresholdManagerSeleniumTest, self).setUp()
        self.go_to('threshold-index')

    def test_datasource_choice(self):
        """Test if selecting a datasource triggers the correct response"""
        dropdown_element = self.driver.find_element_by_id('thresholdDescr')
        select = Select(dropdown_element)
        select.select_by_index(1)

        try:
            self.driver.find_element_by_id('netboxSearchTable')
        except NoSuchElementException:
            self.fail("Select did not trigger display of netbox table")

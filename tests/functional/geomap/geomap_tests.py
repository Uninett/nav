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
"""Testrunner for the geomap page"""

import unittest
from ..mixins import SeleniumMixins
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


class GeoMapSeleniumTests(SeleniumMixins, unittest.TestCase):
    """Tests for the GeoMap page"""

    def setUp(self):
        self.driver = self.get_driver_and_login('admin', 'admin', '/geomap')

    def tearDown(self):
        self.driver.quit()

    def test_map_loaded(self):
        try:
            self.driver.find_element_by_class_name('olMapViewport')
        except NoSuchElementException:
            self.fail('GeoMap seems to not have loaded')


if __name__ == '__main__':
    unittest.main()



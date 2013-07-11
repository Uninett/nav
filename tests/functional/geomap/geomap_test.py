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
from .. import SeleniumTest
from selenium.common.exceptions import NoSuchElementException


class GeoMapSeleniumTests(SeleniumTest):
    """Tests for the GeoMap page"""

    def test_map_loaded(self):
        """Test if map is loaded"""
        try:
            self.driver.find_element_by_class_name('olMapViewport')
        except NoSuchElementException:
            self.fail('GeoMap seems to not have loaded')


if __name__ == '__main__':
    unittest.main()

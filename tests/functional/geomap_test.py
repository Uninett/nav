#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Selenium tests for geomap"""

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


def test_geomap_loaded(selenium, base_url):
    """Test if map is loaded"""
    selenium.get('{}/geomap/'.format(base_url))
    try:
        selenium.find_element(By.CLASS_NAME, 'olMapViewport')
    except NoSuchElementException:
        assert False, 'GeoMap seems to not have loaded'

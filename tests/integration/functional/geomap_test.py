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
"""Playwright tests for geomap"""

from playwright.sync_api import expect


def test_when_loading_geomap_then_map_viewport_should_exist(authenticated_page):
    page, base_url = authenticated_page
    page.goto(f"{base_url}/geomap/")
    expect(page.locator(".olMapViewport")).to_be_visible()

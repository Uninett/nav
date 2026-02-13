#
# Copyright (C) 2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Playwright tests for simple searches on the navbar"""

from playwright.sync_api import expect


def test_when_searching_for_ip_then_it_should_return_result(authenticated_page):
    page, base_url = authenticated_page
    ipaddr = "192.168.42.42"

    page.goto(base_url)
    page.locator("#navbar-search-form #query").fill(ipaddr)
    page.locator("#navbar-search-form button[type='submit']").click()

    expect(page.locator("caption")).to_contain_text(ipaddr)

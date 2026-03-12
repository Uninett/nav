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
"""Playwright tests for arnold"""

import re

from playwright.sync_api import expect


def test_when_visiting_arnold_then_title_should_contain_detentions(authenticated_page):
    page, base_url = authenticated_page
    page.goto(f"{base_url}/arnold/")
    expect(page).to_have_title(re.compile("Detentions"))

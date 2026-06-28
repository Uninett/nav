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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Playwright tests for Status"""

import pytest
from playwright.sync_api import expect


@pytest.fixture
def status_page(authenticated_page):
    page, base_url = authenticated_page
    page.goto(f"{base_url}/status/")
    return page


def test_when_clicking_filter_toggle_then_panel_should_toggle(status_page):
    panel = status_page.locator("#status-panel")
    filter_toggle = status_page.locator(".toggle-panel")

    initial_visible = panel.is_visible()
    filter_toggle.click()

    if initial_visible:
        expect(panel).to_be_hidden()
    else:
        expect(panel).to_be_visible()


def test_when_refreshing_page_then_panel_state_should_persist(status_page):
    panel = status_page.locator("#status-panel")
    filter_toggle = status_page.locator(".toggle-panel")

    expect(panel).to_be_hidden()
    filter_toggle.click()
    expect(panel).to_be_visible()

    # Wait for state to be saved before reloading
    status_page.wait_for_timeout(1000)
    status_page.reload()
    status_page.wait_for_selector("#status-page")

    expect(status_page.locator("#status-panel")).to_be_visible()

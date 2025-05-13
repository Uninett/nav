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
"""Selenium tests for Status"""

from time import sleep
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions


@pytest.fixture
def statuspage(selenium, base_url):
    selenium.get('{}/status/'.format(base_url))
    panel = selenium.find_element(By.ID, 'status-panel')
    filter_toggle = selenium.find_element(By.CLASS_NAME, 'toggle-panel')
    return panel, filter_toggle


def test_panel_should_toggle_when_clicked(statuspage):
    """Test if panel toggles when clicked"""
    panel, filter_toggle = statuspage
    initial_state = panel.is_displayed()
    filter_toggle.click()
    assert initial_state != panel.is_displayed(), (
        'Clicking filter_toggle did not do anything'
    )


def test_remember_last_panel_state(selenium, statuspage):
    """Test if the panel stays in the same state after page refresh"""
    panel, filter_toggle = statuspage
    assert not panel.is_displayed()

    filter_toggle.click()
    sleep(1)
    selenium.refresh()
    WebDriverWait(selenium, 10).until(
        expected_conditions.visibility_of_element_located((By.ID, 'status-page'))
    )
    # We need to fetch panel element again after a refresh
    panel = selenium.find_element(By.ID, 'status-panel')
    assert panel.is_displayed(), 'Panel did not stay in same state after page refresh'

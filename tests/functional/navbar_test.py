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
"""Selenium tests for simple searches on the navbar"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def test_simple_ip_search_should_return_result(selenium, base_url):
    """Tests a search for an IP address"""
    selenium.get('{}/'.format(base_url))
    container = selenium.find_element(By.ID, "navbar-search-form")
    query = container.find_element(By.ID, 'query')
    search_button = container.find_element(By.CSS_SELECTOR, "button[type='submit']")

    ipaddr = "192.168.42.42"
    query.send_keys(ipaddr)
    search_button.click()

    caption = WebDriverWait(selenium, 15).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "caption"), ipaddr)
    )

    caption = selenium.find_element(By.TAG_NAME, 'caption')
    assert ipaddr in caption.text

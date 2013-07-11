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
"""Base functionality for selenium tests"""

import os
import unittest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

BASE_URL = os.environ['TARGETURL']
USERNAME = 'admin'
PASSWORD = os.environ['ADMINPASSWORD']
DEFAULT_WAIT_TIME = 5  # timer for implicit wait in seconds


class SeleniumTest(unittest.TestCase):
    """Super class for selenium tests"""

    def setUp(self):
        self.driver = self.get_driver()
        self.login(self.driver, USERNAME, PASSWORD)

    def tearDown(self):
        self.driver.quit()

    @staticmethod
    def get_driver():
        """Gets selenium driver and navigates to url"""
        driver = webdriver.Firefox()
        driver.implicitly_wait(DEFAULT_WAIT_TIME)  # Poll for x seconds
        driver.get(BASE_URL)
        return driver

    def login(self, driver, username, password):
        """Logs in to NAV"""
        driver.find_element_by_class_name('login').click()
        driver.find_element_by_id('id_username').send_keys(username)
        driver.find_element_by_id('id_password').send_keys(password)
        driver.find_element_by_css_selector('input[type=submit]').click()
        try:
            driver.find_element_by_class_name('logout')
        except NoSuchElementException:
            self.fail('Failed to log in')

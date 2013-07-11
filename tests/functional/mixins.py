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
"""Mixins for selenium tests"""

import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

BASE_URL = os.environ['TARGETURL']


class SeleniumMixins(object):
    """Mixin class for common selenium operations"""

    base_url = 'http://localhost:8080'

    @staticmethod
    def get_driver_and_login(username, password, url='', wait=5):
        """Gets driver and logs in"""
        driver = SeleniumMixins.get_driver(BASE_URL, wait)
        SeleniumMixins.login(driver, username, password)
        driver.get(SeleniumMixins.base_url + url)
        return driver

    @staticmethod
    def get_driver(url, wait):
        """Gets selenium driver and navigates to url"""
        driver = webdriver.Firefox()
        driver.implicitly_wait(wait)  # Poll for x seconds
        driver.get(url)
        return driver

    @staticmethod
    def login(driver, username, password):
        """Logs in to NAV"""
        driver.find_element_by_class_name('login').click()
        driver.find_element_by_id('id_username').send_keys(username)
        driver.find_element_by_id('id_password').send_keys(password)
        driver.find_element_by_css_selector('input[type=submit]').click()
        try:
            driver.find_element_by_class_name('logout')
        except NoSuchElementException:
            self.fail('Failed to log in')

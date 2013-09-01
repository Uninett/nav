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
# pylint: disable=C0103, R0904
"""Base functionality for selenium tests

To run the tests set the following environment variables:
TARGETURL: complete url to the NAV web page to run tests on
ADMINPASSWORD: the password for the admin user in your NAV installation
SELENIUMSERVER: If you need to run the tests on a remote testserver,
                enter the url here.

To set up seleniumserver:
- http://selenium.googlecode.com/files/selenium-server-standalone-2.33.0.jar
- java -jar selenium-server-standalone-2.33.0.jar
- url to server is in output when starting server

"""

from __future__ import absolute_import

import os
import sys
import unittest
import pytest
from django.core.urlresolvers import reverse
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urlparse import urljoin

os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'
BASE_URL = os.environ['TARGETURL']
USERNAME = 'admin'
PASSWORD = os.environ['ADMINPASSWORD']
DEFAULT_WAIT_TIME = 5  # timer for implicit wait in seconds
SCREENSHOT_DIRECTORY = '.selenium_screenshots'


class SeleniumTest(unittest.TestCase):
    """Super class for selenium tests"""

    currentResult = None
    screenshot = None

    def setUp(self):
        """Common tasks to do before each test"""
        self.driver = self.get_driver()
        self.login(self.driver, USERNAME, PASSWORD)

    def tearDown(self):
        """Common tasks to do after each test"""
        if 'WORKSPACE' in os.environ and sys.exc_info()[0]:
            self.save_screenshot()
        self.driver.quit()

    def save_screenshot(self):
        """Save screenshot of a failed test"""
        directory = get_screenshot_directory()
        filename = "%s.%s.png" % (self.__class__.__name__,
                                  self.currentResult.name)
        self.screenshot = os.path.join(directory, filename)
        self.driver.save_screenshot(self.screenshot)

    def run(self, result=None):
        self.currentResult = result
        unittest.TestCase.run(self, result)

    @staticmethod
    def get_driver():
        """Gets selenium driver and navigates to url"""
        if 'SELENIUMSERVER' in os.environ:
            driver = webdriver.Remote(
                command_executor=os.environ['SELENIUMSERVER'],
                desired_capabilities=DesiredCapabilities.FIREFOX)
        else:
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
            self.tearDown()
            pytest.skip('Login failed')

    def go_to(self, viewname):
        """Tell the driver to go to the url with the given viewname"""
        self.driver.get(self.get_url(viewname))

    @staticmethod
    def get_url(viewname):
        """Get url based on viewname"""
        return urljoin(BASE_URL, reverse(viewname))


def get_screenshot_directory():
    """Create and/or get the path to the screenshots for failed tests"""
    directory = os.path.join(os.environ['WORKSPACE'],
                             SCREENSHOT_DIRECTORY,
                             os.environ['BUILD_ID'])
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

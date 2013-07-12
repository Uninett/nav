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
# pylint: disable=C0111, R0904
"""Selenium tests for arnold"""

from .. import SeleniumTest


class ArnoldSeleniumTest(SeleniumTest):
    """Testrunner for the Arnold page"""

    def test_should_default_to_detained_ports(self):
        self.driver.get(self.get_url('arnold_index'))
        title = self.driver.title
        self.assertTrue('Detentions' in title)

    def test_add_quarantine_vlan(self):
        self.driver.get(self.get_url('arnold-quarantinevlans'))

        # Submit a new quarantine vlan
        form = self.driver.find_element_by_css_selector('.tabcontent form')
        form.find_element_by_id('id_vlan').send_keys('10')
        form.find_element_by_id('id_description').send_keys('test')
        form.find_element_by_css_selector('input[type=submit]').click()

        # After submit
        table = self.driver.find_element_by_css_selector(
            '.tabcontent .listtable')
        row = table.find_elements_by_tag_name('tr')[-1]
        self.assertTrue('10' in row.text)
        self.assertTrue('test' in row.text)

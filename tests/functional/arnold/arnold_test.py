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
"""Selenium tests for arnold"""

from .. import SeleniumTest, BASE_URL


class ArnoldTest(SeleniumTest):
    """Testrunner for Arnold selenium tests"""

    def setUp(self):
        super(ArnoldTest, self).setUp()
        self.url = BASE_URL + '/arnold'

    def test_should_default_to_detained_ports(self):
        self.driver.get(self.url)
        title = self.driver.title
        self.assertTrue('Detentions' in title)

    def test_add_quarantine_vlan(self):
        self.driver.get(self.url + '/addquarantinevlan')

        # Submit a new quarantine vlan
        form = self.driver.find_element_by_css_selector('.tabcontent form')
        form.find_element_by_id('id_vlan').send_keys('10')
        form.find_element_by_id('id_description').send_keys('test')
        form.find_element_by_css_selector('input[type=submit]').click()

        # After submit
        table = self.driver.find_element_by_css_selector(
            '.tabcontent listtable')
        row = table.find_elements_by_tag_name('tr')[-1]
        self.assertIn('10', row.text)
        self.assertIn('test', row.text)

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
# pylint:  disable=C0111
"""Tests for config module"""
from __future__ import unicode_literals

import unittest
from configparser import NoOptionError
from nav.config import NAVConfigParser
from nav.ipdevpoll.config import (get_job_sections, get_jobs,
                                  get_job_descriptions, JobDescriptor)


class ConfigTest(unittest.TestCase):
    class TestConfig(NAVConfigParser):
        DEFAULT_CONFIG = """
[job_one]
interval = 5m
plugins = foo
description:
 blapp
 blupp
[job_two]
interval = 5m
plugins = foo
descriptio= blapp
[not_a_job]
interval = 5m
plugins = foo
description=blipp
[job_three]
interval = 5m
plugins = foo
description = blepp
"""

    def setUp(self):
        self.config = self.TestConfig()

    def test_find_all_job_sections(self):
        self.assertEqual(len(get_job_sections(self.config)), 3)

    def test_should_not_fail_on_missing_description(self):
        try:
            get_jobs(self.config)
        except NoOptionError:
            self.fail('Failed to ignore missing option')

    def test_job_prefix_must_be_filtered(self):
        descriptions = get_job_descriptions(self.config)
        for desc in descriptions:
            self.assertFalse(desc.startswith('job_'))

    def test_description_should_not_contain_newline(self):
        descr = get_job_descriptions(self.config)
        self.assertEqual(descr['one'], 'blapp blupp')

    def test_job_two_descr(self):
        self.assertEqual(get_job_descriptions(self.config)['two'],'')

    def test_job_three_descr(self):
        self.assertEqual(get_job_descriptions(self.config)['three'],
                         'blepp')


class JobDescriptorTest(unittest.TestCase):
    class TestConfig(NAVConfigParser):
        DEFAULT_CONFIG = """
[job_one]
plugins = foo
[job_two]
interval = 0
plugins = foo
[job_negative]
interval = -5m
plugins = foo
[job_noplugins]
interval = 5m
[job_emptyplugins]
interval = 5m
plugins =

"""

    def setUp(self):
        self.config = self.TestConfig()

    def test_should_raise_on_no_interval(self):
        self.assertRaises(
            NoOptionError,
            JobDescriptor.from_config_section, self.config, 'job_one')

    def test_should_raise_on_zero_interval(self):
        self.assertRaises(
            ValueError,
            JobDescriptor.from_config_section, self.config, 'job_two')

    def test_should_raise_on_negative_interval(self):
        self.assertRaises(
            ValueError,
            JobDescriptor.from_config_section, self.config, 'job_negative')

    def test_should_raise_on_no_plugins(self):
        self.assertRaises(
            NoOptionError,
            JobDescriptor.from_config_section, self.config, 'job_noplugins')

    def test_should_raise_on_empty_plugins(self):
        self.assertRaises(
            ValueError,
            JobDescriptor.from_config_section, self.config, 'job_emptyplugins')

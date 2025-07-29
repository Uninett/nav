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
"""Tests for config module"""

from configparser import NoOptionError

import pytest

from nav.config import NAVConfigParser
from nav.ipdevpoll.config import (
    get_job_sections,
    get_jobs,
    get_job_descriptions,
    JobDescriptor,
)


@pytest.fixture
def config():
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

    return TestConfig()


class TestConfig(object):
    def test_find_all_job_sections(self, config):
        assert len(get_job_sections(config)) == 3

    def test_should_not_fail_on_missing_description(self, config):
        try:
            get_jobs(config)
        except NoOptionError:
            self.fail('Failed to ignore missing option')

    def test_job_prefix_must_be_filtered(self, config):
        descriptions = get_job_descriptions(config)
        for desc in descriptions:
            assert not desc.startswith('job_')

    def test_description_should_not_contain_newline(self, config):
        descr = get_job_descriptions(config)
        assert descr['one'] == 'blapp blupp'

    def test_job_two_descr(self, config):
        assert get_job_descriptions(config)['two'] == ''

    def test_job_three_descr(self, config):
        assert get_job_descriptions(config)['three'] == 'blepp'


@pytest.fixture
def invalid_config():
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

    return TestConfig()


class TestJobDescriptor(object):
    def test_should_raise_on_no_interval(self, invalid_config):
        with pytest.raises(NoOptionError):
            JobDescriptor.from_config_section(invalid_config, 'job_one')

    def test_should_raise_on_zero_interval(self, invalid_config):
        with pytest.raises(ValueError):
            JobDescriptor.from_config_section(invalid_config, 'job_two')

    def test_should_raise_on_negative_interval(self, invalid_config):
        with pytest.raises(ValueError):
            JobDescriptor.from_config_section(invalid_config, 'job_negative')

    def test_should_raise_on_no_plugins(self, invalid_config):
        with pytest.raises(NoOptionError):
            JobDescriptor.from_config_section(invalid_config, 'job_noplugins')

    def test_should_raise_on_empty_plugins(self, invalid_config):
        with pytest.raises(ValueError):
            JobDescriptor.from_config_section(invalid_config, 'job_emptyplugins')

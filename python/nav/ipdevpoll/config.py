# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
"""ipdevpoll configuration management"""

import os
import logging
import ConfigParser
from StringIO import StringIO

import nav.buildconf
from nav.errors import GeneralException

_logger = logging.getLogger(__name__)

_ipdevpoll_conf_defaults = """
[ipdevpoll]
logfile = ipdevpolld.log

[plugins]

[jobs]

[prefix]
ignored = 127.0.0.0/8, fe80::/16
"""

class IpdevpollConfig(ConfigParser.ConfigParser):
    def __init__(self):
        ConfigParser.ConfigParser.__init__(self)
        # TODO: perform sanity check on config settings
        faked_default_file = StringIO(_ipdevpoll_conf_defaults)
        self.readfp(faked_default_file)
        self.read_all()

    def read_all(self):
        """Read all known ipdevpoll.conf instances."""
        configfile = 'ipdevpoll.conf'
        filenames = [os.path.join(nav.buildconf.sysconfdir, configfile),
                     os.path.join('.', configfile)]
        files_read = self.read(filenames)

        if files_read:
            _logger.debug("Read config files %r", files_read)
        else:
            _logger.warning("Found no config files")
        return files_read

def get_jobs(config=None):
    """Returns a list of JobDescriptors for each of the jobs configured in
    ipdevpoll.conf

    """
    if config is None:
        config = ipdevpoll_conf

    job_prefix = 'job_'
    job_sections = [s for s in config.sections() if s.startswith(job_prefix)]
    job_descriptors = [JobDescriptor.from_config_section(config, section)
                       for section in job_sections]
    _logger.debug("parsed jobs from config file: %r",
                 [j.name for j in job_descriptors])
    return job_descriptors

class JobDescriptor(object):
    """A data structure describing a job."""
    def __init__(self, name, interval, intensity, plugins):
        self.name = str(name)
        self.interval = int(interval)
        self.intensity = int(intensity)
        self.plugins = list(plugins)

    @classmethod
    def from_config_section(cls, config, section):
        """Creates a JobDescriptor from a ConfigParser section"""
        job_prefix = 'job_'
        if section.startswith(job_prefix):
            jobname = section[len(job_prefix):]
        else:
            raise InvalidJobSectionName(section)

        interval = (config.has_option(section, 'interval') and
                    _parse_time(config.get(section, 'interval')) or '')
        intensity = (config.has_option(section, 'intensity') and
                     config.getint(section, 'intensity') or 0)
        plugins = (config.has_option(section, 'plugins') and
                    _parse_plugins(config.get(section, 'plugins')) or '')

        return cls(jobname, interval, intensity, plugins)

def _parse_time(value):
    value = value.strip()

    if value == '':
        return 0

    if value.isdigit():
        return int(value)

    value, unit = int(value[:-1]), value[-1:].lower()

    if unit == 'd':
        return value * 60*60*24
    elif unit == 'h':
        return value * 60*60
    elif unit == 'm':
        return value * 60
    elif unit == 's':
        return value

    raise GeneralException('Invalid time format: %s%s' % (value, unit))

def _parse_plugins(value):
    if value:
        return value.split()

    return []

class ConfigurationError(GeneralException):
    """Configuration error"""
    pass

class InvalidJobSectionName(ConfigurationError):
    """Section name is invalid as a job section"""

ipdevpoll_conf = IpdevpollConfig()


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
"""
FIXME
"""

import os
import logging
import ConfigParser

import nav.path
from nav.config import getconfig
from nav.errors import GeneralException

logger = logging.getLogger(__name__)

def get_jobs(config=None):
    if config is None:
        config = ConfigParser.ConfigParser()
        config.read([os.path.join(nav.path.sysconfdir, 'jobs.conf'), 'jobs.conf'])
    jobs = {}

    for section in config.sections():
        interval = config.has_option(section, 'interval') and \
            parse_time(config.get(section, 'interval')) or ''
        plugins  = config.has_option(section, 'plugins') and \
            parse_plugins(config.get(section, 'plugins', '')) or ''

        if interval and plugins:
            jobs[section] = (interval, plugins)
            logger.debug("Registered job in registry: %s", section)

    return jobs

def parse_time(value):
    value = value.strip()

    if value == '':
        return 0

    if value.isdigit():
        return int(value)

    value,unit = int(value[:-1]), value[-1:].lower()

    if unit == 'd':
        return value * 60*60*24
    elif unit == 'h':
        return value * 60*60
    elif unit == 'm':
        return value * 60
    elif unit == 's':
        return value

    raise GeneralException('Invalid time format: %s%s' % (value, unit))

def parse_plugins(value):
    if value:
        return value.split()

    return []

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

import logging

import nav.path
from nav.config import getconfig
from nav.errors import GeneralException

logger = logging.getLogger(__name__)

def get_jobs():
    config = getconfig('jobs.conf', configfolder=nav.path.sysconfdir)
    jobs = {}

    for section,settings in config.items():
        interval = parse_time(settings.get('interval', ''))
        plugins  = parse_plugins(settings.get('plugins', ''))

        if interval and plugins:
            jobs[section] = (interval, plugins)
            logger.debug("Registered job in registry: %s", section)

    # FIXME add dependencies of plugins to array (possibly switch to a set
    # while we are at it.

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

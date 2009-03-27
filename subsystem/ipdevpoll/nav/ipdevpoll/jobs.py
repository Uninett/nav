"""
FIXME
"""
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

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

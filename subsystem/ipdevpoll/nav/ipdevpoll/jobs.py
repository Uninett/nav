"""
FIXME
"""
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

import logging
from ConfigParser import ConfigParser

import nav.path
from nav.errors import GeneralException

logger = logging.getLogger(__name__)

def get_jobs():
    jobs =  {}

    config = ConfigParser()
    config.read('jobs.conf') # FIXME use nav.path

    for section in config.sections():
        interval = config.get(section, 'interval')
        plugins = config.get(section, 'plugins').split()

        interval = get_time(interval)

        if interval and plugins:
            jobs[section] = (interval, plugins)
            logger.debug("Registered job in registry: %s", section)

    # FIXME add dependencies of plugins to array (possibly switch to a set
    # while we are at it.

    return jobs

def get_time(value):
    value = value.strip()

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

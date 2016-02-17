#!/usr/bin/env python
#
# Copyright (C) 2016 UNINETT AS
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
"""Sends NAV statistics to the Carbon collector"""

import logging
import os.path
import time

from django.db import connection, DatabaseError

import nav.models
from nav.buildconf import localstatedir
from nav.config import NAVConfigParser
from nav.logs import set_log_levels
from nav.metrics.carbon import send_metrics
from nav.metrics.names import escape_metric_name

_logger = logging.getLogger('bin.stats')
LOGFILE = 'stats.log'


class StatsCollectorConfig(NAVConfigParser):
    """Configparser for Netbiostracker"""
    DEFAULT_CONFIG_FILES = ('stats.conf',)


def main():
    init_logging()
    config = StatsCollectorConfig()
    collect_stats(config)


def init_logging():
    """Initialize logging to file"""
    set_log_levels()

    handler = logging.FileHandler(os.path.join(localstatedir, 'log', LOGFILE))
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] '
                                  '[%(name)s] %(message)s')
    handler.setFormatter(formatter)
    root = logging.getLogger('')
    root.addHandler(handler)


def collect_stats(config):
    """Collect stats with given config

    :type config: StatsCollectorConfig
    """
    _logger.info('--> Starting stats collection <--')

    for section in config.sections():
        _logger.info("Collecting statistic %s", section)
        try:
            collect(config.get(section, 'path'), config.get(section, 'query'))
        except DatabaseError as error:
            _logger.error('Error collecting stats for %s: %s', section, error)

    _logger.info('--> Stats collection done <--')


def collect(metric_path_fmt, query):
    """Collect and store a statistic based on the result of the query

    :param metric_path_fmt: The metric path format to use. Note that the
    number of columns in the result of the query must match the format.
    :param query: SQL query to run to get values
    """

    assert metric_path_fmt and query

    timestamp = int(time.time())

    with connection.cursor() as cursor:
        cursor.execute(query)
        metrics = [create_metric(result, metric_path_fmt, timestamp)
                   for result in cursor.fetchall()]
    send_metrics(metrics)


def create_metric(result, metric_path_fmt, timestamp):
    """Create a metric ready for sending to carbon

    :param result: the database row
    :param metric_path_fmt: a string format to turn into a metric path
    :param timestamp: timestamp used in metric
    :return: a metric tuple suitable for sending to carbon
    """
    args = [escape_metric_name(x) for x in result[:-1]]
    metric_path = metric_path_fmt.format(*args)
    value = result[-1]
    _logger.debug('%s - %s:%s', metric_path, timestamp, value)
    return metric_path, (timestamp, value)


if __name__ == '__main__':
    main()

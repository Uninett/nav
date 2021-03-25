#!/usr/bin/env python
#
# Copyright (C) 2012 Uninett AS
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
"""Counts active ip-addresses in a prefix and stores the data in rrd-files"""

import logging
import time

from django.db import connection

_logger = logging.getLogger(__name__)


def collect(days=None):
    """Collect data from database

    Use either a quick query for updates only, or a slow one for walking
    through historic data.
    """

    starttime = time.time()
    intervals = get_intervals(days) if days else 0

    if intervals:
        _logger.debug('Collecting %s intervals', intervals)
        query = get_interval_query(intervals)
    else:
        query = get_static_query()

    _logger.debug(query)

    cursor = connection.cursor()
    cursor.execute(query)

    _logger.debug('Query executed in %.2f seconds', time.time() - starttime)

    return cursor.fetchall()


def get_interval_query(intervals):
    """Return query for collecting data for a time interval"""

    query = (
        """
    SELECT
        netaddr,
        timeentry,
        COUNT(DISTINCT ip) AS ipcount,
        COUNT(DISTINCT mac) AS maccount
    FROM vlan
    JOIN prefix USING (vlanid)
    CROSS JOIN (
        SELECT
            now() - generate_series(0,%s) * INTERVAL '30 minutes' AS timeentry)
        AS series
    LEFT JOIN arp ON (
        ip << netaddr AND
        (timeentry >= start_time AND timeentry <= end_time))
    WHERE vlan.nettype NOT IN ('loopback') AND ip IS NOT NULL
    GROUP BY netaddr, timeentry
    ORDER BY timeentry
    """
        % intervals
    )

    return query


def get_static_query():
    """Return for query for doing a static collection"""
    query = """
    SELECT
        netaddr,
        now() AS timeentry,
        COUNT(DISTINCT ip) AS ipcount,
        COUNT(DISTINCT mac) AS maccount
    FROM vlan
    JOIN prefix USING (vlanid)
    LEFT JOIN arp ON (ip << netaddr AND arp.end_time = 'infinity')
    WHERE vlan.nettype NOT IN ('loopback')
    GROUP BY netaddr, timeentry
    ORDER BY timeentry
    """

    return query


def get_intervals(days):
    """Return number of intervals in given days"""
    intervals_in_day = 2 * 24
    return days * intervals_in_day

#!/usr/bin/env python
#
# Copyright (C) 2012 UNINETT AS
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
"""Counts active ip-addresses in a prefix and stores the data in rrd-files"""

import logging
import time

from django.db import connection

LOG = logging.getLogger('ipcollector.collector')

def collect(days=None):
    """Collect data from database

    netaddr: a list of prefixes to collect from
    when: a datetime.datetime object
    """

    intervals = get_intervals(days) if days else 0

    starttime = time.time()
    LOG.debug('Collecting %s intervals' % intervals)

    query = """
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
    WHERE vlan.nettype NOT IN ('loopback')
    GROUP BY netaddr, timeentry
    ORDER BY timeentry
    """ % intervals

    LOG.debug(query)

    cursor = connection.cursor()
    cursor.execute(query)

    LOG.debug('Query executed in %.2f seconds' % (time.time() - starttime))

    return cursor.fetchall()


def get_intervals(days):
    """Return number of intervals in given days"""
    intervals_in_day = 2 * 24
    return days * intervals_in_day

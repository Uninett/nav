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
"""Provides functions for fetching prefix related data in the API"""

from IPy import IP

from django.db import connection
from django.urls import reverse


class UsageResult(object):
    """Container for creating usage results for serializing"""

    def __init__(self, prefix, active_addresses, starttime=None, endtime=None):
        """

        :type prefix: manage.Prefix
        :type active_addresses: int
        :type starttime: datetime.datetime
        :type endtime: datetime.datetime
        """
        self.prefix = prefix.net_address
        self.active_addresses = active_addresses
        self.max_addresses = IP(self.prefix).len()
        self.max_hosts = self.max_addresses - 2
        self.usage = self.active_addresses / float(self.max_hosts) * 100
        self.starttime = starttime
        self.net_ident = prefix.vlan.net_ident
        self.vlan_id = prefix.vlan.vlan
        self.endtime = endtime if self.starttime else None
        self.url_machinetracker = reverse(
            'machinetracker-prefixid_search_active', args=[prefix.pk]
        )
        self.url_report = prefix.get_absolute_url()
        self.url_vlan = reverse('vlan-details', args=[prefix.vlan.pk])


def fetch_usages(prefixes, starttime, endtime):
    """Fetch usage for a list of prefixes"""
    if prefixes is None:
        prefixes = []
    return [fetch_usage(prefix, starttime, endtime) for prefix in prefixes]


def fetch_usage(prefix, starttime, endtime):
    """Fetches usage for the prefix

    :param prefix: the prefix to fetch active addresses from
    :type prefix: manage.Prefix
    :type starttime: datetime.datetime
    :type endtime: datetime.datetime
    """
    result = collect_active_ip(prefix, starttime, endtime)
    return UsageResult(prefix, result, starttime, endtime)


def collect_active_ip(prefix, starttime=None, endtime=None):
    """Collects active ip based on prefix and optional starttime and endtime

    :param prefix: prefix to find active ip addresses for
    :type prefix: manage.Prefix

    :param starttime: if set will query for active ip-addresses at that time.
                      if set with endtime indicates the start of the window
                      for finding active ip addresses
    :type starttime: datetime.datetime

    :param endtime: if set indicates the end of the window for finding
                    active ip addresses
    :type endtime: datetime.datetime

    :returns: int -- an integer representing the active addresses
    """

    cursor = connection.cursor()
    basequery = "SELECT COUNT(DISTINCT ip) AS ipcount FROM arp"
    prefix = prefix.net_address

    if starttime and endtime:
        query = (
            basequery
            + """
        WHERE (ip << %s AND (start_time, end_time) OVERLAPS (%s, %s))
        """
        )
        cursor.execute(query, (prefix, starttime, endtime))
    elif starttime:
        query = (
            basequery
            + """
        WHERE (ip << %s AND %s BETWEEN start_time AND end_time)
        """
        )
        cursor.execute(query, (prefix, starttime))
    else:
        query = (
            basequery
            + """
        WHERE (ip << %s AND end_time >= 'infinity')
        """
        )
        cursor.execute(query, (prefix,))

    result = cursor.fetchone()
    return int(result[0])

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
# ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#

import re
from datetime import date, datetime, timedelta
from socket import gethostbyaddr, herror

from django.utils.datastructures import SortedDict

def hostname(addr):
    dns = _Hostname()
    return dns.lookup(addr)

class _Hostname:
    cache = {}

    def lookup(self, addr):
        if addr in self.cache:
            return self.cache[addr]
        try:
            dns = gethostbyaddr(addr)
        except herror:
            return False
        self.cache[addr] = dns[0]
        return dns[0]

def min_max_mac(mac):
    """If max is shorter than 12 characters we pad the mac with 0 for the
    min_mac and f for the max_mac.

    Ie. if mac is 00:10:20:40
    mac_min will be 00:10:20:40:00:00
    mac_max will be 00:10:20:40:ff:ff
    """
    mac = re.sub("[^0-9a-fA-F]+", "", mac).lower()
    if len(mac) < 12:
        mac_min = mac + '0' * (12 - len(mac))
        mac_max = mac + 'f' * (12 - len(mac))
    else:
        mac_min = mac
        mac_max = mac
    return (mac_min, mac_max)
    

def track_mac(keys, resultset, dns):
    """Groups results from Query for the mac_search page.

        keys        - a tuple/list with strings that identifies the fields the
                      result should be grouped by
        resultset   - a QuerySet
        dns         - should we lookup the hostname?
    """
    tracker = SortedDict()
    for row in resultset:
        if row['end_time'] > datetime.now():
            row['still_active'] = "Still active"
        if dns:
            row['dns_lookup'] = hostname(row['ip'])
        key = []
        for k in keys:
            key.append(row.get(k))
        key = tuple(key)
        if key not in tracker:
            tracker[key] = []
        tracker[key].append(row)
    return tracker

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
from IPy import IP

from django.utils.datastructures import SortedDict

from nav import asyncdns
from nav.models.manage import Prefix

_cached_hostname = {}
def hostname(ip):
    addr = unicode(ip)
    if addr in _cached_hostname:
        return _cached_hostname[addr]

    try:
        dns = gethostbyaddr(addr)
    except herror:
        return False

    _cached_hostname[addr] = dns[0]
    return dns[0]

def from_to_ip(from_ip, to_ip):
    from_ip = IP(from_ip)
    if to_ip:
        to_ip = IP(to_ip)
    else:
        to_ip = from_ip
    return (from_ip, to_ip)

def get_prefix_info(addr):
    try:
        return Prefix.objects.select_related().extra(
        select={"mask_size": "masklen(netaddr)"},
        where=["%s << netaddr AND nettype <> 'scope'"],
        order_by=["-mask_size"],
        params=[addr])[0]
    except:
        return None


def ip_dict(rows):
    result = SortedDict()
    for row in rows:
        ip = IP(row.ip)
        if ip not in result:
            result[ip] = []
        result[ip].append(row)
    return result

def process_ip_row(row, dns):
    if row.end_time > datetime.now():
        row.still_active = "Still active"
    if dns:
        row.dns_lookup = hostname(row.ip) or ""
    return row

def min_max_mac(mac):
    """If max is shorter than 12 characters we pad the mac with 0 for the
    min_mac and f for the max_mac.

    Ie. if mac is 00:10:20:40
    mac_min will be 00:10:20:40:00:00
    mac_max will be 00:10:20:40:ff:ff
    """
    mac = re.sub("[^0-9a-fA-F]+", "", mac).lower()
    mac_min = mac + '0' * (12 - len(mac))
    mac_max = mac + 'f' * (12 - len(mac))
    return (mac_min, mac_max)

def track_mac(keys, resultset, dns):
    """Groups results from Query for the mac_search page.

        keys        - a tuple/list with strings that identifies the fields the
                      result should be grouped by
        resultset   - a QuerySet
        dns         - should we lookup the hostname?
    """
    if dns:
        ips_to_lookup = [row['ip'] for row in resultset]
        dns_lookups = asyncdns.reverse_lookup(ips_to_lookup)

    tracker = SortedDict()
    for row in resultset:
        if row['end_time'] > datetime.now():
            row['still_active'] = "Still active"
        if dns:
            if not isinstance(dns_lookups[row['ip']], Exception):
                row['dns_lookup'] = dns_lookups[row['ip']].pop()
            else:
                row['dns_lookup'] = ""
        if 'module' not in row or not row['module']:
            row['module'] = ''
        if 'port' not in row or not row['port']:
            row['port'] = ''
        key = []
        for k in keys:
            key.append(row.get(k))
        key = tuple(key)
        if key not in tracker:
            tracker[key] = []
        tracker[key].append(row)
    return tracker

class ProcessInput:
    def __init__(self, input):
        self.input = input.copy()

    def __common(self):
        if not self.input.get('days', False):
            self.input['days'] = 7

    def __prefix(self):
        try:
            ip = Prefix.objects.get(id=self.input['prefixid'])
        except Prefix.DoesNotExist:
            return None
        subnet = IP(ip.net_address)
        self.input['from_ip'] = unicode(subnet[0])
        self.input['to_ip'] = unicode(subnet[-1])

    def ip(self):
        if self.input.get('prefixid', False):
            self.__prefix()
        self.__common()
        if not self.input.get('active', False) and not self.input.get('inactive', False):
            self.input['active'] = "on"
        return self.input

    def mac(self):
        self.__common()
        return self.input

    def swp(self):
        self.__common()
        return self.input

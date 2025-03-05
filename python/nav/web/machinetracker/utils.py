#
# Copyright (C) 2009-2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Common utility functions for Machine Tracker"""

from datetime import datetime
from socket import gethostbyaddr, herror
from collections import namedtuple, OrderedDict
import logging

from IPy import IP

from django.db import DatabaseError, transaction

from nav import asyncdns
from nav.models.manage import Prefix, Netbox, Interface

_cached_hostname = {}
_logger = logging.getLogger(__name__)


def hostname(ip):
    """
    Performs a DNS reverse lookup for an IP address and caches the result in
    a global variable, which is really, really stupid.

    :param ip: And IP address string.
    :returns: A hostname string or a False value if the lookup failed.

    """
    addr = str(ip)
    if addr in _cached_hostname:
        return _cached_hostname[addr]

    try:
        dns = gethostbyaddr(addr)
    except herror:
        return False

    _cached_hostname[addr] = dns[0]
    return dns[0]


@transaction.atomic()
def get_prefix_info(addr):
    """Returns the smallest prefix from the NAVdb that an IP address fits into.

    :param addr: An IP address string.
    :returns: A Prefix object or None if no prefixes matched.

    """
    try:
        return Prefix.objects.select_related().extra(
            select={"mask_size": "masklen(netaddr)"},
            where=["%s << netaddr AND nettype <> 'scope'"],
            order_by=["-mask_size"],
            params=[addr],
        )[0]
    except (IndexError, DatabaseError):
        return None


def get_last_job_log_from_netboxes(rows, job_type):
    """Returns a dict with netbox object as key and job_log object as value.

    Takes rows and a job type as parameters.
    The rows should needs a .netbox object on them from eg. CAM or ARP.
    The job_type is a string with job type such as 'ip2mac' or 'topo'

    """
    netboxes_job = dict((row.netbox, None) for row in rows if row.netbox)
    for netbox in netboxes_job:
        try:
            netboxes_job[netbox] = netbox.job_log.filter(job_name=job_type).order_by(
                '-end_time'
            )[0]
        except IndexError:
            pass
    return netboxes_job


def normalize_ip_to_string(ipaddr):
    """Normalizes an IP address to a a sortable string.

    When sending IP addresses to a browser and asking JavaScript to sort them
    as strings, this function will help.

    An IPv4 address will be normalized to '4' + <15-character dotted quad>.
    An IPv6 address will be normalized to '6' + <39 character IPv6 address>

    """
    try:
        ipaddr = IP(ipaddr)
    except ValueError:
        return ipaddr

    if ipaddr.version() == 4:
        quad = str(ipaddr).split('.')
        return '4%s' % '.'.join([i.zfill(3) for i in quad])
    else:
        return '6%s' % ipaddr.strFullsize()


def ip_dict(rows):
    """Converts IP search result rows to a dict keyed by IP addresses.

    :param rows: IP search result rows.
    :return: A dict mapping IP addresses to matching result rows.
    """
    result = OrderedDict()
    for row in rows:
        ip = IP(row.ip)
        if ip not in result:
            result[ip] = []
        result[ip].append(row)
    return result


def process_ip_row(row, dns):
    """Processes an IP search result row"""
    if row.end_time > datetime.now():
        row.still_active = "Still active"
    if dns:
        row.dns_lookup = hostname(row.ip) or ""
    return row


def min_max_mac(prefix):
    """Finds the minimum and maximum MAC addresses of a given prefix.

    :returns: A tuple of (min_mac_string, max_mac_string)

    """
    return str(prefix[0]), str(prefix[-1])


def track_mac(keys, resultset, dns):
    """Groups results from Query for the mac_search page.

    keys        - a tuple/list with strings that identifies the fields the
                  result should be grouped by
    resultset   - a QuerySet
    dns         - should we lookup the hostname?
    """
    if dns:
        ips_to_lookup = {row.ip for row in resultset}
        _logger.debug(
            "track_mac: looking up PTR records for %d addresses)", len(ips_to_lookup)
        )
        dns_lookups = asyncdns.reverse_lookup(ips_to_lookup)
        _logger.debug("track_mac: PTR lookup done")

    tracker = OrderedDict()
    for row in resultset:
        if row.end_time > datetime.now():
            row.still_active = "Still active"
        if dns:
            ip = row.ip
            if dns_lookups[ip] and not isinstance(dns_lookups[ip], Exception):
                row.dns_lookup = dns_lookups[ip].pop()
            else:
                row.dns_lookup = ""
        if not hasattr(row, 'module'):
            row.module = ''
        if not hasattr(row, 'port'):
            row.port = ''
        key = []
        for k in keys:
            key.append(getattr(row, k))
        key = tuple(key)
        if key not in tracker:
            tracker[key] = []
        tracker[key].append(row)
    return tracker


def get_vendor_query(mac_field='mac'):
    """Return a query that populates vendor names on a query.

    This needs a field with a MAC address to match against the oui table.
    The field containing the mac address can be specified with the `mac_field`
    parameter.

    Ex:
    Arp.objects.filter(..).extra(select={'vendor': get_vendor_query()})"""
    return f"SELECT vendor from oui where oui=trunc({mac_field})"


class ProcessInput:
    """Some sort of search form input processing class. Who the hell knows."""

    def __init__(self, forminput):
        """
        :type forminput:  django.http.QueryDict
        """
        self.input = forminput.copy()

    def __common(self):
        if not self.input.get('days', False):
            self.input['days'] = 7

    def ip(self):
        """Populates the GET dict with formatted values for an ip search"""
        self.__common()
        if not self.input.get('period_filter'):
            self.input['period_filter'] = 'active'

        return self.input

    def mac(self):
        """Populates the GET dict with formatted values for a mac search"""
        self.__common()
        return self.input

    def swp(self):
        """Populates the GET dict with formatted values for a switch search"""
        self.__common()
        return self.input

    def netbios(self):
        """Populates the GET dict with formatted values for a netbios search"""
        self.__common()
        return self.input


UplinkTuple = namedtuple('UplinkTuple', 'mac sysname uplink vendor')


class UplinkTracker(list):
    def __init__(self, mac_min, mac_max, vendor=False):
        boxes = Netbox.objects.extra(
            select={'mac': 'netboxmac.mac'},
            tables=['netboxmac'],
            where=[
                'netboxmac.netboxid=netbox.netboxid',
                'netboxmac.mac BETWEEN %s AND %s',
            ],
            params=[mac_min, mac_max],
        ).order_by('mac', 'sysname')

        if vendor:
            boxes = boxes.extra(select={'vendor': get_vendor_query()})

        for box in boxes:
            uplinks = box.get_uplinks()
            box_vendor = box.vendor if vendor else None
            if uplinks:
                for link in uplinks:
                    self.append(UplinkTuple(box.mac, box.sysname, link, box_vendor))
            else:
                self.append(UplinkTuple(box.mac, box.sysname, None, box_vendor))


class InterfaceTracker(list):
    def __init__(self, mac_min, mac_max, vendor=False):
        ifcs = (
            Interface.objects.select_related('netbox')
            .extra(where=['ifphysaddress BETWEEN %s AND %s'], params=[mac_min, mac_max])
            .order_by('ifphysaddress', 'netbox__sysname')
        )
        if vendor:
            ifcs = ifcs.extra(select={'vendor': get_vendor_query('ifphysaddress')})
        self.extend(ifcs)

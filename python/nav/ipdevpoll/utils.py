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
"""Utility functions for ipdevpoll."""

import logging
import gc

from IPy import IP

import django.db
from django.conf import settings

_logger = logging.getLogger(__name__)

def binary_mac_to_hex(binary_mac):
    """Converts a binary string MAC address to hex string.

    Only the first 6 octets will be converted, any more will be
    ignored. If the address contains less than 6 octets, the result will be
    padded with leading zeros.

    """
    if binary_mac:
        if len(binary_mac) < 6:
            binary_mac = "\x00" * (6 - len(binary_mac)) + binary_mac
        return ":".join("%02x" % ord(x) for x in binary_mac[:6])

def truncate_mac(mac):
    """Takes a MAC address on the form xx:xx:xx... of any length and returns
    the first 6 parts.
    """
    parts = mac.split(':')
    if len(parts) > 6:
        mac = ':'.join(parts[:6])
    return mac

def find_prefix(ip, prefix_list):
    """Takes an IPy.IP object and a list of manage.Prefix and returns the most
    precise prefix the IP matches.
    """
    ret = None
    for p in prefix_list:
        sub = IP(p.net_address)
        if ip in sub:
            # Return the most precise prefix, ie the longest prefix
            if not ret or IP(ret.net_address).prefixlen() < sub.prefixlen():
                ret = p
    return ret

def is_invalid_utf8(string):
    """Returns True if string is invalid UTF-8.

    If string is not a an str object, or is decodeable as UTF-8, False is
    returned.

    """
    if isinstance(string, str):
        try:
            string.decode('utf-8')
        except UnicodeDecodeError, e:
            return True
    return False

def django_debug_cleanup():
    """Resets Django's list of logged queries.

    When DJANGO_DEBUG is set to true, Django will log all generated SQL queries
    in a list, which grows indefinitely.  This is ok for short-lived processes;
    not so much for daemons.  We may want those queries in the short-term, but
    in the long-term the ever-growing list is uninteresting and also bad.

    This should be called once-in-a-while from every thread that has Django
    database access, as the queries list is stored in thread-local data.

    """
    query_count = len(django.db.connection.queries)
    if query_count:
        _logger.debug("Removing %d logged Django queries", query_count)
        django.db.reset_queries()
        gc.collect()



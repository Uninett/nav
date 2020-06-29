#
# Copyright (C) 2014 Uninett AS
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
"""Provides a function for getting host information"""


import IPy
from django.utils.lru_cache import lru_cache
from nav import asyncdns

from nav.util import is_valid_ip


def address_sorter(addr_tuple):
    """Return ip object from tuple"""
    return IPy.IP(addr_tuple[0])


def forward_lookup(host):
    """Do a forward lookup on host"""
    addrinfo = asyncdns.forward_lookup([host])
    if not isinstance(addrinfo[host], Exception):
        return set(addr for addr in addrinfo[host])


def reverse_lookup(addresses):
    """Do a reverse lookup on addresses"""
    reverses = asyncdns.reverse_lookup(addresses)
    for addr, response in sorted(reverses.items(), key=address_sorter):
        if isinstance(response, Exception):
            yield {'addr': addr, 'error': response.__class__.__name__}
        else:
            for name in response:
                yield {'addr': addr, 'name': name}


def _get_host_info(host):
    """Returns a dictionary containing DNS information about the host"""
    if is_valid_ip(host, strict=True):
        addresses = list(reverse_lookup([host]))
    else:
        try:
            addresses = forward_lookup(host) or []
        except UnicodeError:
            # Probably just some invalid string that cannot be represented using IDNA
            # encoding. Let's just pretend it never happened (i.e. we can't look it up)
            addresses = []
        if addresses:
            addresses = list(reverse_lookup(addresses))

    return {'host': host, 'addresses': addresses}


get_host_info = lru_cache()(_get_host_info)

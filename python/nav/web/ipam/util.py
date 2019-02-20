# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Uninett AS
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

"""
API and prefixes related utilities
"""

import ipaddress
from nav.models.manage import Prefix
from django.db.models import Q
from IPy import IP, IPSet


class PrefixQuerysetBuilder(object):
    """Utility class to build queryset(s) for Prefix. Returns the resulting
    queryset when finalize() is called.

    """

    def __init__(self, queryset=None):
        if queryset is None:
            queryset = Prefix.objects.all()
        self.queryset = queryset
        self.is_realized = False
        self.post_hooks = [lambda x: x]

    def filter(self, origin, *args, **kwargs):
        """Works like queryset.filter, but returns self and short-circuits on
        'None' origin

        """
        if origin is not None and origin:
            self.queryset = self.queryset.filter(*args, **kwargs)
        return self

    def finalize(self):
        "Returns the queryset with all filters applied"
        # Apply post-hooks before returning final result
        for fn in self.post_hooks:
            self.queryset = fn(self.queryset)
        return self.queryset

    # Filter methods
    def organization(self, org):
        "Fuzzy match prefix on VLAN organization"
        return self.filter(org, vlan__organization__id=org)

    def filter_full_prefixes(self):
        """Remove /32 (or /128) prefixes from the queryset. Often useful to
        reduce noise, as these are of little or no value to most network
        planning operations.

        Returns:
            A lazy iterator of all filtered prefixes

        """
        def _filter_full_prefixes(q):
            for prefix in q:
                ip = IP(prefix.net_address)
                if ip.version() == 4 and ip.prefixlen() < 32:
                    yield prefix
                    continue
                if ip.version() == 6 and ip.prefixlen() < 128:
                    yield prefix
                    continue
        self.post_hooks.append(_filter_full_prefixes)
        return self

    def description(self, descr):
        "Fuzzy match prefix on VLAN description"
        return self.filter(descr, vlan__description__icontains=descr)

    def vlan_number(self, vlan_number):
        "Return prefixes belonging to a particular VLAN"
        if vlan_number is None and vlan_number:
            return self
        return self.filter(vlan_number, vlan__vlan=vlan_number)

    def net_type(self, net_type_or_net_types):
        "Return prefixes only of the given type(s)"
        if net_type_or_net_types is None or not net_type_or_net_types:
            return self
        types = net_type_or_net_types
        if not isinstance(types, list):
            types = [types]
        return self.filter(types, vlan__net_type__in=types)

    def search(self, query):
        """Fuzzy search prefixes with query on VLAN description or
        organization

        """
        new_query = Q()
        new_query.add(Q(vlan__description__icontains=query), Q.OR)
        new_query.add(Q(vlan__organization__id__icontains=query), Q.OR)
        return self.filter(query, new_query)

    def usage(self, usage):
        "Return prefixes based on their VLAN's usage field"
        return self.filter(usage, vlan__usage__id=usage)

    # Mutating methods, e.g. resets the queryset
    def within(self, prefix):
        "Sets the queryset to every Prefix within a certain prefix"
        if prefix is not None and prefix:
            self.queryset = self.queryset & Prefix.objects.within(prefix)
        return self

    def contains_ip(self, addr):
        "Returns all prefixes containing the given address"
        try:
            ip = IP(addr)
        except (ValueError, TypeError):
            return self
        new_query = Prefix.objects.contains_ip(ip.strNormal())
        self.queryset = self.queryset & new_query
        return self


# Code finding available subnets
def get_available_subnets(prefix_or_prefixes):
    """Get available prefixes within a list of CIDR addresses, based on
    prefixes found in NAV.

    Args:
        prefix_or_prefixes: a single or a list of prefixes ("10.0.0.0/8") or
                          IPy.IP objects

    Returns:
           An iterable IPy.IPSet of available addresses.

    """
    if not isinstance(prefix_or_prefixes, list):
        prefix_or_prefixes = [prefix_or_prefixes]
    base_prefixes = [str(prefix) for prefix in prefix_or_prefixes]
    all_used_prefixes = []
    for prefix in base_prefixes:
        # Query NAV to get prefixes within the current base prefix
        used_prefixes = PrefixQuerysetBuilder().within(prefix).finalize()
        for used_prefix in used_prefixes:
            all_used_prefixes.append(used_prefix.net_address)
    return _get_available_subnets(prefix_or_prefixes, all_used_prefixes)


def _get_available_subnets(prefix_or_prefixes, used_prefixes):
    """Get available prefixes within a list of CIDR addresses, based on what
    prefixes are in use. E.g. this is `get_available_subnets`, but with
    explicit dependency injection.

    Args:
        prefix_or_prefixes: a single or a list of prefixes ("10.0.0.0/8") or
                          IPy.IP objects
        used_prefixes: prefixes that are in use

    Returns:
           An iterable IPy.IPSet of available addresses within prefix_or_prefixes

    """
    if not isinstance(prefix_or_prefixes, list):
        prefix_or_prefixes = [prefix_or_prefixes]
    base_prefixes = [str(prefix) for prefix in prefix_or_prefixes]
    acc = IPSet([IP(prefix) for prefix in prefix_or_prefixes])
    used_prefixes = IPSet([IP(used) for used in used_prefixes])
    # remove used prefixes
    acc.discard(used_prefixes)
    # filter away original prefixes
    return sorted([ip for ip in acc if str(ip) not in base_prefixes])


def partition_subnet(prefixlen, prefix):
    "Partition prefix into subnets with room for at at least n hosts"
    net = ipaddress.ip_network(prefix)
    return (IP(subnet.with_prefixlen) for
            subnet in net.subnets(new_prefix=prefixlen))


def suggest_range(prefix, prefixlen=24, offset=0, n=10):
    """Partitions prefix into blocks of 'n' hosts. Returns a list of
    [startAddr, endAddr, prefix]

    Args:
        prefix: a string (e.g. "10.0.0.0/8") or IPy.IP object
        size: the minimum number of addresses in each subnet
        offset: how many candidates to skip (from start)
        n: number of results desired

    Returns:
        A dictionary with information about the original query, as well as a
        list of candidates (subnets) of the requires size.

        {"prefix": "10.0.32.0/19",
         "requested_size": 257,
         "offset": 0,
         "more": true
         "candidates": [
             "10.0.32.0/24",
             "10.0.33.0/24",
             ...
         ]}

    """
    acc = {
        "prefix": prefix,
        "prefixlen": prefixlen,
        "candidates": [],
        "offset": offset,
        "more": True
    }
    # Fast path: size > size of network, so just return the original prefix
    _prefix = IP(prefix)
    if prefixlen < _prefix.prefixlen():
        _blocks = iter([_prefix])
    # Somewhat slow path
    else:
        _blocks = partition_subnet(prefixlen, prefix)
    try:
        # drop first #offset blocks
        for _ in range(offset):
            next(_blocks)
        # collect remainder
        for block in (next(_blocks) for _ in range(n)):
            acc["candidates"].append({
                "length": block.len(),
                "prefix": str(block),
                "start": str(block[-0]),
                "end": str(block[-1])
            })
    except StopIteration:
        # done, set "more" flag
        acc["more"] = False
    return acc

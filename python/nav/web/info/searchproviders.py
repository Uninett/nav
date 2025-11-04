#
# Copyright (C) 2012 (SD -311000) Uninett AS
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

"""Module containing different searchproviders used for searching in NAV"""

from collections import namedtuple

from django.db.models import Q, Count
from django.urls import reverse

from IPy import IP

from nav.models.manage import (
    Room,
    Location,
    Netbox,
    Interface,
    Vlan,
    UnrecognizedNeighbor,
    NetboxGroup,
)
from nav.util import is_valid_ip
from nav.web.ipdevinfo.views import is_valid_hostname
from nav.web.info.prefix.views import get_query_results as get_prefix_results


SearchResult = namedtuple("SearchResult", ['href', 'inst'])


class SearchProvider(object):
    """Search provider interface.

    To implement this interface, all that is needed is to inherit from this
    class, set some class attributes and override the fetch_results() method.
    The query, as entered by the end-user will be available in the
    ``self.query`` variable.
    """

    name = "SearchProvider"
    """Used as the caption of results from this provider"""

    headers = (('Column title', 'result instance attribute name'),)
    """Defines the result table columns; what the column titles should be,
    and which attribute from the SearchResult.inst object to extract the
    values for this column from. """

    link = 'id'
    """The title of the result column to put hyperlinks in"""

    def __init__(self, query=""):
        """
        :param query: The search query string, as entered by the user.
        """
        self.results = []
        self.query = query
        self.fetch_results()

    def fetch_results(self):
        """Fetches and returns results based on ``self.query``.

        :returns: A list of :py:class:`nav.web.info.searchproviders.SearchResult`
        instances.
        """
        raise NotImplementedError


class RoomSearchProvider(SearchProvider):
    """Searchprovider for rooms"""

    name = "Rooms"
    headers = [('Roomid', 'id'), ('Description', 'description')]
    link = 'Roomid'

    def fetch_results(self):
        results = Room.objects.filter(
            Q(id__icontains=self.query) | Q(description__icontains=self.query)
        ).order_by("id")
        for result in results:
            self.results.append(
                SearchResult(reverse('room-info', kwargs={'roomid': result.id}), result)
            )


class LocationSearchProvider(SearchProvider):
    """Searchprovider for locations"""

    name = "Locations"
    headers = [('Locationid', 'id'), ('Description', 'description')]
    link = 'Locationid'

    def fetch_results(self):
        results = Location.objects.filter(
            Q(id__icontains=self.query) | Q(description__icontains=self.query)
        ).order_by("id")
        for result in results:
            self.results.append(
                SearchResult(
                    reverse('location-info', kwargs={'locationid': result.id}), result
                )
            )


class NetboxSearchProvider(SearchProvider):
    """Searchprovider for netboxes"""

    name = "IP devices"
    headers = [('Sysname', 'sysname'), ('IP', 'ip')]
    link = 'Sysname'

    def fetch_results(self):
        if is_valid_ip(self.query, strict=True):
            results = Netbox.objects.filter(ip=self.query)
        else:
            results = Netbox.objects.filter(sysname__icontains=self.query)

        results.order_by("sysname")
        for result in results:
            self.results.append(
                SearchResult(
                    reverse(
                        'ipdevinfo-details-by-name', kwargs={'name': result.sysname}
                    ),
                    result,
                )
            )


class InterfaceSearchProvider(SearchProvider):
    """Searchprovider for interfaces"""

    name = "Interfaces"
    headers = [
        ('IP Device', 'netbox.sysname'),
        ('Interface', 'ifname'),
        ('Alias', 'ifalias'),
    ]
    link = 'Interface'

    def fetch_results(self):
        results = Interface.objects.filter(
            Q(ifalias__icontains=self.query) | Q(ifname__icontains=self.query)
        ).order_by('netbox__sysname', 'ifindex')

        for result in results:
            self.results.append(
                SearchResult(
                    reverse(
                        'ipdevinfo-interface-details',
                        kwargs={
                            'netbox_sysname': result.netbox.sysname,
                            'port_id': result.id,
                        },
                    ),
                    result,
                )
            )


class FallbackSearchProvider(SearchProvider):
    """Fallback searchprovider if no results are found.

    Two cases:
    1 - if ip, send to ipdevinfos name lookup
    2 - if valid text based on ipdevinfos regexp, send to ipdevinfo
    """

    name = "Fallback"

    def fetch_results(self):
        ip_address = is_valid_ip(self.query)
        if ip_address:
            self.results.append(
                SearchResult(
                    reverse('ipdevinfo-details-by-addr', kwargs={'addr': ip_address}),
                    None,
                )
            )
        elif is_valid_hostname(self.query):
            self.results.append(
                SearchResult(
                    reverse('ipdevinfo-details-by-name', kwargs={'name': self.query}),
                    None,
                )
            )


class VlanSearchProvider(SearchProvider):
    """Searchprovider for vlans"""

    name = "Vlans"
    headers = [
        ('Vlan', 'vlan'),
        ('Type', 'net_type'),
        ('Netident', 'net_ident'),
        ('Description', 'description'),
    ]
    link = 'Vlan'

    def fetch_results(self):
        results = (
            Vlan.objects.exclude(net_type='loopback')
            .filter(
                Q(vlan__contains=self.query)
                | Q(net_ident__icontains=self.query)
                | Q(net_type__description__icontains=self.query)
                | Q(description__icontains=self.query)
            )
            .order_by('vlan')
        )
        for result in results:
            self.results.append(
                SearchResult(
                    reverse('vlan-details', kwargs={'vlanid': result.id}), result
                )
            )


class PrefixSearchProvider(SearchProvider):
    """Searchprovider for prefixes"""

    name = "Prefix"
    headers = [('Prefix', 'net_address'), ('Vlan', 'vlan')]
    link = 'Prefix'

    def fetch_results(self):
        """Returns the prefixes determined by the query"""
        try:
            IP(self.query)  # Validate query
        except ValueError:
            pass
        else:
            self.results = [
                SearchResult(p.get_absolute_url(), p)
                for p in get_prefix_results(self.query)
            ]


class UnrecognizedNeighborSearchProvider(SearchProvider):
    """Search provider for Unrecognized neighbor entries"""

    name = "Unrecognized neighbors"
    headers = [
        ('Remote id', 'remote_id'),
        ('Remote name', 'remote_name'),
        ('Seen on', 'interface'),
        ('Source', 'source'),
    ]
    link = 'Seen on'

    def fetch_results(self):
        results = UnrecognizedNeighbor.objects.filter(
            Q(remote_id__contains=self.query) | Q(remote_name__contains=self.query)
        ).order_by('remote_id', 'remote_name')

        self.results = [
            SearchResult(result.interface.get_absolute_url(), result)
            for result in results
        ]


class DevicegroupSearchProvider(SearchProvider):
    """Searchprovider for device group entries"""

    name = "Device groups"
    headers = [('Device Group', 'id'), ('# netboxes', 'num_netboxes')]
    link = 'Device Group'

    def fetch_results(self):
        query_result = (
            NetboxGroup.objects.filter(
                Q(id__icontains=self.query) | Q(description__icontains=self.query)
            )
            .order_by('id')
            .annotate(num_netboxes=Count('netboxes'))
        )
        self.results = [SearchResult(g.get_absolute_url(), g) for g in query_result]

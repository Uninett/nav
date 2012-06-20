#
# Copyright (C) 2012 (SD -311000) UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.core.urlresolvers import reverse

from nav.models.manage import Room, Netbox
from nav.util import is_valid_ip
from nav.web.ipdevinfo.views import is_valid_hostname

class SearchResult():
    """
    Container for searchresults
    """
    def __init__(self, text, href, inst=None):
        self.text = text
        self.href = href
        self.inst = inst


class SearchProvider(object):
    """
    Searchprovider interface
    """
    name = "SearchProvider"

    def __init__(self, query=""):
        self.results = []
        self.query = query
        self.fetch_results()

    def fetch_results(self):
        """ Fetch results for the query """
        pass


class RoomSearchProvider(SearchProvider):
    """
    Searchprovider for rooms
    """
    name = "Rooms"

    def fetch_results(self):
        results = Room.objects.filter(id__icontains=self.query).order_by("id")
        for result in results:
            self.results.append(SearchResult(result.id,
                reverse('room-info', kwargs={'roomid': result.id}), result))


class NetboxSearchProvider(SearchProvider):
    """
    Searchprovider for netboxes
    """
    name = "Netboxes"

    def fetch_results(self):
        if is_valid_ip(self.query):
            results = Netbox.objects.filter(ip=self.query)
        else:
            results = Netbox.objects.filter(sysname__icontains=self.query)

        results.order_by("sysname")
        for result in results:
            self.results.append(SearchResult(result.sysname,
                reverse('ipdevinfo-details-by-name',
                    kwargs={'name': result.sysname}), result))


class FallbackSearchProvider(SearchProvider):
    """
    Fallback searchprovider if no results are found.
    Two cases:
    1 - if ip, send to ipdevinfos name lookup
    2 - if valid text based on ipdevinfos regexp, send to ipdevinfo
    """
    name = "Fallback"

    def fetch_results(self):
        if is_valid_ip(self.query):
            self.results.append(
                SearchResult(self.query, reverse('ipdevinfo-details-by-addr',
                    kwargs={'addr': self.query}), None))
        elif is_valid_hostname(self.query):
            self.results.append(
                SearchResult(self.query, reverse('ipdevinfo-details-by-name',
                    kwargs={'name': self.query}), None))

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


import re
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.models.manage import Room, Netbox
from nav.util import is_valid_ip
from nav.web.info.forms import SearchForm
from nav.web.ipdevinfo.views import is_valid_hostname


class SearchResult():
    """
    Container for searchresults
    """
    def __init__(self, text, href, inst):
        self.text = text
        self.href = href
        self.inst = inst


class SearchProvider():
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


def index(request):
    """
    Main controller
    """
    searchproviders = []

    if "query" in request.GET:
        form = SearchForm(request.GET, auto_id=False)
        if form.is_valid():
            searchproviders = process_form(form)
            if has_only_one_result(searchproviders):
                return HttpResponseRedirect(searchproviders[0].results[0].href)
    else:
        form = SearchForm()

    return render_to_response("info/base.html",
            {"form": form,
             "searchproviders": searchproviders},
        context_instance=RequestContext(request)
    )


def process_form(form):
    """
    Processor for searchform on main page
    """
    query = form.cleaned_data['query']

    searchproviders = [RoomSearchProvider(query), NetboxSearchProvider(query)]
    providers_with_result = has_results(searchproviders)
    if not providers_with_result:
        fallback = FallbackSearchProvider(query)
        if fallback.results:
            providers_with_result.append(fallback)

    return providers_with_result


def has_results(searchproviders):
    """
    Check if any of the searchproviders has any results
    """
    providers_with_result = []
    for searchprovider in searchproviders:
        if searchprovider.results:
            providers_with_result.append(searchprovider)

    return providers_with_result


def has_only_one_result(searchproviders):
    """
    Check if searchproviders has one and only one result
    """
    return len(searchproviders) == 1 and len(searchproviders[0].results) == 1

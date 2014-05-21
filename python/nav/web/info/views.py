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
"""Views for /info"""

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from nav.web.info.forms import SearchForm
from nav.web.info.searchproviders import (RoomSearchProvider,
                                          NetboxSearchProvider,
                                          FallbackSearchProvider,
                                          InterfaceSearchProvider,
                                          VlanSearchProvider)
from nav.web.utils import create_title

from random import choice


def get_path():
    """Get the path for this subsystem"""
    return [('Home', '/'), ('Search', reverse('info-search'))]


def index(request):
    """Main controller"""

    searchproviders = []

    navpath = [('Home', '/'), ('Search', reverse('info-search'))]
    titles = navpath

    if "query" in request.GET:
        form = SearchForm(request.GET, auto_id=False)
        if form.is_valid():
            titles.append(('Search for "%s"' % request.GET["query"],))
            searchproviders = process_form(form)
            if has_only_one_result(searchproviders):
                return HttpResponseRedirect(searchproviders[0].results[0].href)
    else:
        form = SearchForm()

    return render_to_response("info/base.html",
                              {"form": form,
                               "searchproviders": searchproviders,
                               "navpath": navpath,
                               "title": create_title(titles)},
                              context_instance=RequestContext(request))


def process_form(form):
    """Processor for searchform on main page"""
    query = form.cleaned_data['query']

    if not query:
        return []

    searchproviders = [RoomSearchProvider(query),
                       NetboxSearchProvider(query),
                       InterfaceSearchProvider(query),
                       VlanSearchProvider(query)]
    providers_with_result = has_results(searchproviders)
    if not providers_with_result:
        fallback = FallbackSearchProvider(query)
        if fallback.results:
            providers_with_result.append(fallback)

    return providers_with_result


def has_results(searchproviders):
    """Check if any of the searchproviders has any results"""
    providers_with_result = []
    for searchprovider in searchproviders:
        if searchprovider.results:
            providers_with_result.append(searchprovider)

    return providers_with_result


def has_only_one_result(searchproviders):
    """Check if searchproviders has one and only one result"""
    results = 0
    for provider in searchproviders:
        results += len(provider.results)
    return results == 1


def osm_map_redirecter(_, zoom, ytile, ztile):
    """A redirector for OpenStreetmap tiles"""
    server = choice(['a', 'b', 'c'])
    url = "http://%s.tile.openstreetmap.org/%s/%s/%s.png" % (
        server, zoom, ytile, ztile)
    return redirect(url, permanent=True)

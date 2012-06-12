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


from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.web.info.forms import SearchForm
from nav.web.info.searchproviders import RoomSearchProvider, NetboxSearchProvider, FallbackSearchProvider


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

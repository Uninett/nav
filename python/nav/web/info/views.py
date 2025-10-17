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
#
"""Views for /info"""

import importlib
import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
from django_htmx.http import trigger_client_event

from nav.web.info.forms import SearchForm
from nav.web.info import searchproviders as providers
from nav.web.modals import render_modal
from nav.web.utils import create_title

_logger = logging.getLogger(__name__)


def get_path():
    """Get the path for this subsystem"""
    return [('Home', '/'), ('Search', reverse('info-search'))]


def index(request):
    """Main controller"""

    searchproviders = []
    failed_providers = []

    navpath = [('Home', '/'), ('Search', reverse('info-search'))]
    titles = navpath

    if "query" in request.GET:
        form = SearchForm(request.GET, auto_id=False)
        if form.is_valid():
            titles.append(('Search for "%s"' % request.GET["query"],))
            searchproviders, failed_providers = process_form(form)
            if has_only_one_result(searchproviders) and not failed_providers:
                return HttpResponseRedirect(searchproviders[0].results[0].href)
    else:
        form = SearchForm()

    return render(
        request,
        "info/base.html",
        {
            "form": form,
            "searchproviders": searchproviders,
            "failed_providers": failed_providers,
            "navpath": navpath,
            "title": create_title(titles),
        },
    )


def index_search_preview(request):
    """
    Renders a preview of search results for the navbar search form.

    Returns an HTTP response with the rendered search results and triggers
    the appropriate client event for the popover.
    """
    query = request.GET.get("query")
    form = SearchForm(request.GET, auto_id=False)
    if not (query and form.is_valid()):
        return _render_search_results(request, query=query, show_results=False)

    search_providers, failed_providers = process_form(form)
    if has_only_one_result(search_providers) and not failed_providers:
        provider = search_providers[0]
        if provider.name == 'Fallback':
            return _render_search_results(request, query=query)

    for provider in search_providers:
        count = len(provider.results)
        provider.count = count
        if count > 5:
            provider.results = provider.results[:5]
            provider.truncated = True
            provider.truncated_count = count - 5

    return _render_search_results(
        request,
        results=search_providers,
        query=query,
    )


def _render_search_results(request, results=None, query=None, show_results=True):
    """Render search results"""

    response = render(
        request,
        "info/_navbar_search_results.html",
        {"results": results, "query": query or '', "show_results": show_results},
    )
    event = "popover.open" if show_results else "popover.close"
    return trigger_client_event(
        response,
        event,
        {
            'id': 'navbar-search-form',
        },
    )


def process_form(form):
    """Processor for searchform on main page"""
    query = form.cleaned_data['query']

    if not query:
        return [], []

    providers_with_errors = []
    searchproviders = []
    for providerpath in settings.SEARCHPROVIDERS:
        modulestring, functionstring = providerpath.rsplit('.', 1)
        try:
            providermodule = importlib.import_module(modulestring)
            provider = getattr(providermodule, functionstring)
            searchproviders.append(provider(query))
        except (AttributeError, ImportError) as error:
            providers_with_errors.append((providerpath, error))
            _logger.error('Could not import %s', providerpath)
        except Exception as error:  # noqa: BLE001
            providers_with_errors.append((providerpath, error))
            _logger.exception(
                "Search provider raised unhandled exception: %s", providerpath
            )

    providers_with_result = has_results(searchproviders)
    if not providers_with_result and not providers_with_errors:
        fallback = providers.FallbackSearchProvider(query)
        if fallback.results:
            providers_with_result.append(fallback)

    return providers_with_result, providers_with_errors


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


def image_help_modal(request):
    """View for image help modal"""
    return render_modal(
        request, "info/_image_help_modal.html", modal_id="image-help", size="small"
    )

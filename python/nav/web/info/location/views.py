#
# Copyright (C) 2017 Uninett AS
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
"""View functions for the locationinfo subsystem"""

import logging

from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from nav.models.manage import Location
from nav.web.info.forms import SearchForm
from nav.web.info.images.upload import handle_image_upload
from nav.web.utils import create_title


CATEGORIES = ("GW", "GSW", "SW", "EDGE")

_logger = logging.getLogger('nav.web.info.location')


class LocationSearchForm(SearchForm):
    """Searchform for locations"""

    def __init__(self, *args, **kwargs):
        super(LocationSearchForm, self).__init__(
            *args, form_action='location-search', placeholder='Location', **kwargs
        )


def get_path():
    """Get the path for this subsystem"""
    return [
        ('Home', '/'),
        ('Search', reverse('info-search')),
        ('Location', reverse('location-search')),
    ]


def search(request):
    """Controller for searching for locations"""
    navpath = get_path()

    locations = Location.objects.none()
    titles = navpath

    if "query" in request.GET:
        searchform = LocationSearchForm(request.GET, auto_id=False)
        if searchform.is_valid():
            titles.append(("Search for %s" % request.GET['query'],))
            locations = process_searchform(searchform)
    else:
        searchform = LocationSearchForm()

    if request.htmx:
        return render(
            request,
            "info/location/_search_results.html",
            {
                "searchform": searchform,
                "locations": locations,
            },
        )

    return render(
        request,
        "info/location/base.html",
        {
            "searchform": searchform,
            "locations": locations,
            "navpath": navpath,
            "title": create_title(titles),
        },
    )


def process_searchform(form):
    """Find and return locations based on searchform"""
    query = form.cleaned_data['query']
    if query is None:
        return Location.objects.all()
    else:
        return Location.objects.filter(
            Q(id__icontains=query)
            | Q(description__icontains=query)
            | Q(child_locations__id__icontains=query)
        ).order_by("id")


def locationinfo(request, locationid):
    """Controller for displaying locationinfo"""
    location = get_object_or_404(Location, id=locationid)
    navpath = get_path() + [(location.id,)]
    location.sorted_data = sorted(location.data.items())

    return render(
        request,
        "info/location/locationinfo.html",
        {
            "location": location,
            "navpath": navpath,
            "images": location.images.all(),
            "title": create_title(navpath),
        },
    )


def upload_image(request, locationid):
    """Controller for uploading an image"""

    location = get_object_or_404(Location, pk=locationid)
    navpath = get_path() + [
        (location.id, reverse('location-info', kwargs={'locationid': location.id})),
        ('Edit images',),
    ]

    if request.method == 'POST':
        _logger.debug('Uploading images')
        handle_image_upload(request, location=location)
        return redirect("location-info-upload", locationid=location.id)

    return render(
        request,
        "info/location/upload.html",
        {"object": location, "navpath": navpath, "title": create_title(navpath)},
    )

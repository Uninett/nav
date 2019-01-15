#
# Copyright (C) 2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controllers for displaying the neighbor app"""

import logging

from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render

from nav.models.manage import UnrecognizedNeighbor
from nav.web.utils import create_title

_logger = logging.getLogger(__name__)


def index(request):
    """Controller for rendering the main page of neighbors"""
    return render_unrecognized(request)


def render_unrecognized(request):
    """Render unrecognized neighbors"""
    context = {
        'neighbors': UnrecognizedNeighbor.objects.select_related(
            'interface__netbox'),
        'page': 'unrecognized'
    }

    return render_page(request, context)


def render_page(request, extra_context):
    """Render the page with a given context"""
    navpath = [('Home', '/'), ('Unrecognized Neighbors', )]
    context = {
        'navpath': navpath,
        'title': create_title(navpath),
    }
    context.update(extra_context)
    return render(request, 'neighbors/base.html', context)


def set_ignored_state(request):
    """Set ignored on a neighbor instance"""
    if request.method == 'POST':
        ids = request.POST.getlist('neighborids[]')
        action = request.POST.get('action')

        _logger.debug('%s %s', action, ids)

        neighbors = UnrecognizedNeighbor.objects.filter(pk__in=ids)
        if action == 'ignore':
            neighbors.update(ignored_since=datetime.now())
            response = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            neighbors.update(ignored_since=None)
            response = ''
        return HttpResponse(response)

    return HttpResponse("Wrong request method", status=400)

#
# Copyright (C) 2015 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
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
import json

from datetime import datetime
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from nav.models.manage import UnrecognizedNeighbor
from nav.web.utils import create_title

_logger = logging.getLogger(__name__)


def index(request):
    """Controller for rendering the main page of neighbors"""
    return render_unrecognized(request)


def render_unrecognized(request):
    """Render unrecognized neighbors"""
    context = {
        'neighbors': UnrecognizedNeighbor.objects.filter(
            ignored_since__isnull=True),
        'page': 'unrecognized'
    }

    return render_page(request, context)


def render_ignored(request):
    """Render ignored neighbors"""
    context = {
        'neighbors': UnrecognizedNeighbor.objects.filter(
            ignored_since__isnull=False),
        'page': 'ignored'
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
    """Set ignored state on a neighbor instance"""
    if request.method == 'POST':
        nid = request.POST.get('neighborid')
        ignored = json.loads(request.POST.get('ignored'))

        _logger.debug('set_ignored_state: %s %s', nid, ignored)

        neighbor = get_object_or_404(UnrecognizedNeighbor, pk=nid)
        if ignored:
            neighbor.ignored_since = datetime.now()
        else:
            neighbor.ignored_since = None
        neighbor.save()
        return HttpResponse()

    return HttpResponse("Wrong request method", status=400)



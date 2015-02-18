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

_logger = logging.getLogger(__name__)


def index(request):
    """Controller for rendering the main page of neighbors"""

    context = {
        'neighbors': UnrecognizedNeighbor.objects.filter(
            ignored_since__isnull=True),
    }
    return render(request, 'neighbors/base.html', context)


def set_ignored_state(request):
    """Set ignored state on a neighbor instance"""

    if request.method == 'POST':
        pk = request.POST.get('neighborid')
        ignored = json.loads(request.POST.get('ignored'))

        _logger.debug('set_ignored_state: %s %s', pk, ignored)

        neighbor = get_object_or_404(UnrecognizedNeighbor, pk=pk)
        if ignored:
            neighbor.ignored_since = datetime.now()
        else:
            neighbor.ignored_since = None
        neighbor.save()
        return HttpResponse()

    return HttpResponse("Wrong request method", status=400)


def render_tbody(request):
    """Renders the body of a table with unrecognized neighbors"""

    ignored = json.loads(request.REQUEST.get('ignored'))
    ignored_reversed = not ignored
    _logger.debug('render_tbody: %s %s', ignored, ignored_reversed)
    context = {
        'neighbors': UnrecognizedNeighbor.objects.filter(
            ignored_since__isnull=ignored_reversed)
    }
    return render(request, 'neighbors/frag-tbody.html', context)

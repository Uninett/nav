#
# Copyright 2011 UNINETT AS
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
"""Controllers for threshold app"""

import json
from django.http import HttpResponse
from django.shortcuts import render
from nav.metrics.names import raw_metric_query
from nav.metrics.graphs import get_simple_graph_url


def index(request):
    """Base controller for threshold search"""
    return render(request, 'threshold/base.html')


def threshold_search(request):
    """Returns json formatted searchresult"""
    result = []
    if 'term' in request.GET:
        term = enhance_term(request.GET['term'])
        metrics = get_metrics(term)
        for metric in metrics:
            result.append({
                'label': metric['id'],
                'value': metric['id'],
                'expandable': metric['expandable']
            })

    return HttpResponse(json.dumps(result), content_type='application/json')


def enhance_term(term):
    """Format the term based on certain rules

    :type term: str
    """
    if term.endswith('.'):
        term += '*'

    return term


def get_metrics(term):
    """Get metrics based on search term

    :type term: str
    """
    metrics = raw_metric_query(term)
    if not metrics:
        term += '*'
        metrics = raw_metric_query(term)

    return metrics


def get_graph_url(request):
    """Get graph url based on metric"""
    url = None
    if 'metric' in request.GET:
        url = get_simple_graph_url(request.GET['metric'])
    return HttpResponse(json.dumps({'url': url}),
                        content_type='application/json')

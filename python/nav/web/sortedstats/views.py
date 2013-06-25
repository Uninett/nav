#
# Copyright (C) 2006 Norwegian University of Science and Technology
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Sorted statistics views."""

import logging
from operator import itemgetter
from urllib import urlencode

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse

from nav.metrics.data import get_metric_average

_logger = logging.getLogger(__name__)

TIMEFRAMES = (
    ('-1h', 'Last Hour'),
    ('-1d', 'Last Day'),
    ('-1w', 'Last Week'),
    ('-1month', 'Last Month'),
)

DEFAULT_VALUES = {
    'width': 1046,
    'height': 448,
    'from': '-1d',
    'until': 'now',
    'template': 'nav'
}

VIEWS = {
    'cpu_routers_highestmax': {
        'title': 'CPU Highest Average',
        'data_filter': 'highestAverage({serieslist}, {rows})',
        'graph_filter': 'substr(group({serieslist}),2,3)',
        'serieslist': 'nav.devices.*.cpu.*.loadavg5min',
        'graph_args': {
            'title': 'Routers with highest average cpu load',
            'vtitle': 'Percent'
        }
    },
    'uptime': {
        'title': 'Highest uptime',
        'data_filter': 'highestMax({serieslist}, {rows})',
        'graph_filter': 'substr(scale(group({serieslist}), {scale}), 2,3)',
        'serieslist': 'nav.devices.*.system.sysuptime',
        'scale': '0.000000116',
        'graph_args': {
            'title': 'Network devices with highest uptime',
            'vtitle': 'Time'
        }
    }
}


def fetch_raw_data(viewname, rows, timeframe='-1d'):
    """Fetch raw data from graphite

    :param viewname: which of the VIEWS we are fetching data for
    :param rows: number of rows used in filter functions
    :param timeframe: the from-attribute used in the query
    """
    view = VIEWS[viewname]
    view['rows'] = rows
    view['from'] = timeframe

    args = dict_merge(DEFAULT_VALUES, view)
    args['target'] = view['data_filter'].format(
        serieslist=view['serieslist'], rows=view['rows'])
    result = get_metric_average(args['target'], args['from'], args['until'])
    if 'scale' in view:
        result = upscale(result, float(view['scale']))
    return result


def upscale(result, scale):
    """Upscale the values of the result dictionary with scale

    :param result:
    :param scale:
    """
    return dict((x[0], x[1] * scale) for x in result.items())


def create_graph_url(viewname, raw_data, timeframe='-1d'):
    """Create url for getting a graph from Graphite

    :param viewname: The VIEW we are graphing
    :param raw_data: Data from former query
    :param timeframe: the from attribute used in the query
    """

    view = VIEWS[viewname]
    view_args = view['graph_args']
    view_args['from'] = timeframe

    kwargs = {'serieslist': ",".join(raw_data.keys())}
    if 'scale' in view:
        kwargs['scale'] = view['scale']

    view_args['target'] = view['graph_filter'].format(**kwargs)
    graph_args = dict_merge(DEFAULT_VALUES, view_args)
    return reverse("graphite-render") + "?" + urlencode(graph_args)


def dict_merge(a_dict, b_dict):
    """Merge two dictionaries. b will overwrite a"""
    return dict(a_dict.items() + b_dict.items())


def index(request):
    """Sorted stats search & result view"""
    numrows = int(request.GET.get('numrows', 5))
    fromtime = request.GET.get('fromtime', '-1d')
    sectionslist = [(x[0], x[1]['title']) for x in VIEWS.items()]

    context = {
        'title': 'Statistics',
        'navpath': [('Home', '/'), ('Statistics', False)],
        'numrows': numrows,
        'fromtime': fromtime,
        'timeframes': TIMEFRAMES,
        'sectionslist': sectionslist,
    }

    if 'view' in request.GET:
        view = request.GET['view']
        data = fetch_raw_data(view, numrows, fromtime)
        graph_url = create_graph_url(view, data, fromtime)

        context.update({
            'view': view,
            'view_timeframe': dict(TIMEFRAMES)[fromtime],
            'data': sorted(data.items(), key=itemgetter(1), reverse=True),
            'graph_url': graph_url
        })

    return render_to_response('sortedstats/sortedstats.html', context,
                              context_instance=RequestContext(request))

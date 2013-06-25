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
        'metric_name': [2],
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
        'metric_name': [2],
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
        data = sort_by_value(reformat(data, view))

        context.update({
            'view': view,
            'view_timeframe': dict(TIMEFRAMES)[fromtime],
            'data': data,
            'graph_url': graph_url
        })

    return render_to_response('sortedstats/sortedstats.html', context,
                              context_instance=RequestContext(request))


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
    args['target'] = view['data_filter'].format(**view)
    result = get_metric_average(args['target'], args['from'], args['until'])
    if 'scale' in view:
        result = upscale(result, float(view['scale']))
    return result


def upscale(result, scale):
    """Upscale the values of the result dictionary with scale"""
    return dict((x[0], x[1] * scale) for x in result.items())


def create_graph_url(viewname, raw_data, timeframe='-1d'):
    """Create url for getting a graph from Graphite

    :param viewname: The VIEW we are graphing
    :param raw_data: Data from former query
    :param timeframe: the from attribute used in the query
    """
    view = VIEWS[viewname]
    graph_args = dict_merge(DEFAULT_VALUES, view['graph_args'])
    graph_args['from'] = timeframe

    kwargs = {'serieslist': get_series_list(raw_data)}
    if 'scale' in view:
        kwargs['scale'] = view['scale']

    graph_args['target'] = view['graph_filter'].format(**kwargs)
    return reverse("graphite-render") + "?" + urlencode(graph_args)


def get_series_list(raw_data):
    return ",".join([x[0] for x in sort_by_value(raw_data)])


def sort_by_value(data):
    return sorted(data.items(), key=itemgetter(1), reverse=True)


def dict_merge(a_dict, b_dict):
    """Merge two dictionaries. b will overwrite a"""
    return dict(a_dict.items() + b_dict.items())


def reformat(data, view):
    """Sort and reformat keys according to view"""
    indexes = VIEWS[view]['metric_name']
    new_data = {}
    for key in data.keys():
        metric_names = key.split('.')
        metric_name = " - ".join([metric_names[index] for index in indexes])
        new_data[metric_name] = data[key]

    return new_data

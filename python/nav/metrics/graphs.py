#
# Copyright (C) 2013 UNINETT
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
"""Getting graphs of NAV-collected data from Graphite"""
import re
from urllib import urlencode
from django.core.urlresolvers import reverse

TIMETICKS_IN_DAY = 100 * 3600 * 24

META_LOOKUPS = (

    # Various counter type values

    (re.compile(r'\.ports\.(?P<ifname>[^\.]+)\.(?P<counter>[^\.,\)]+)$'),
     dict(alias='{ifname} {counter}')),

    (re.compile(r'\.if[^.()]+Octets(IPv6)?$'),
     dict(transform="scaleToSeconds(nonNegativeDerivative(scale({id},8)),1)",
          unit="bits/s")),

    (re.compile(r'\.if(In|Out)Errors$'),
     dict(transform="scaleToSeconds(nonNegativeDerivative({id},8),1)",
          unit="errors/s")),

    (re.compile(r'\.if(In|Out)[^\.]*Pkts$'),
     dict(transform="scaleToSeconds(nonNegativeDerivative({id},8),1)",
          unit="packets/s")),

    (re.compile(r'\.sysuptime$'),
     dict(transform="scale({id},%.20f)" % (1.0/TIMETICKS_IN_DAY),
          unit="days")),

    (re.compile(r'\.loadavg[0-9]+min$'), dict(unit="%")),
    (re.compile(r'_percent$'), dict(unit="%")),
    (re.compile(r'\.memory\..*\.(free|used)$'),
     dict(unit="bytes", yUnitSystem="binary")),
    (re.compile(r'\.(roundTripTime|responseTime)$'), dict(unit="seconds")),

)


def get_simple_graph_url(metric_paths, time_frame="1day", title=None,
                         width=480, height=250, **kwargs):
    """
    Returns an URL, fetchable by an end user, to render a simple graph,
    given a Graphite metric known to NAV

    :param metric_paths: One or more graphite metric paths.
    :param time_frame: A time frame for the graph, expressed in units that
                       Graphite can understand, e.g. "6 hours", "1 day" or
                       "2 weeks"
    :param title: A caption to print above the graph.
    :param width: The graph width in pixels.
    :param height: The graph height in pixels.
    :return: The URL that will generate the requested graph.

    """
    if isinstance(metric_paths, basestring):
        metric_paths = [metric_paths]

    args = _get_simple_graph_args(metric_paths, time_frame)
    args.update({
        'width': width,
        'height': height,
        'title': title or '',
    })
    if kwargs:
        args.update(kwargs)

    url = reverse("graphite-render") + "?" + urlencode(args, True)
    return url


def _get_simple_graph_args(metric_paths, time_frame):
    args = {
        'target': [],
        'from': "-%s" % time_frame,
        'template': 'nav',
        'yMin': 0,
    }

    for target in metric_paths:
        meta = get_metric_meta(target)
        target = meta['target']
        if meta['alias']:
            target = 'alias({target}, "{alias}")'.format(
                target=target, alias=meta['alias'])
        args['target'].append(target)
        if meta['unit']:
            args['vtitle'] = meta['unit']
        if meta['yUnitSystem']:
            args['yUnitSystem'] = meta['yUnitSystem']

    return args


def get_metric_meta(metric_path):
    """
    Returns a dict with meta information about a given metric path,
    retrieved from various sources.

    :returns: A dict(id=..., transform=..., target=,..., unit=..., alias=...)
              where `id` equals the given metric path, `transform` is a string
              template that can be used to transform the metric using graphite
              functions, `target` is the transformed metric path that will
              can be used as a graph target, `unit` is the unit specification
              for the resulting target, and `alias` is an alias to use for
              the metric in a graph legend.

    """
    result = dict(id=metric_path, transform=None, target=metric_path, unit=None,
                  description=None, alias=None, yUnitSystem=None)
    for pattern, meta in META_LOOKUPS:
        match = pattern.search(metric_path)
        if match:
            result.update(match.groupdict())
            result.update(meta)

    if result['transform']:
        result['target'] = result['transform'].format(**result)
    if result['alias']:
        result['alias'] = result['alias'].format(**result)
    return result

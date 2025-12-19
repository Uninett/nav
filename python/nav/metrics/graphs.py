#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Getting graphs of NAV-collected data from Graphite"""

import re

from django.urls import reverse
from urllib.parse import urlencode


TIMETICKS_IN_DAY = 100 * 3600 * 24
TARGET_TOKENS = re.compile(r'[\w\-*?]+|[(){}\[\]]|,|\.')


def get_sensor_meta(metric_path):
    """
    Returns meta information for drawing a Sensor metric graph annotated with
    the correct yUnits, among other things.
    """

    from nav.models.manage import Sensor
    from nav.metrics.lookup import lookup

    sensor = lookup(metric_path)
    if not sensor:
        return dict()
    assert isinstance(sensor, Sensor)

    alias = (
        sensor.human_readable.replace("\n", " ")
        if sensor.human_readable
        else sensor.name
    )
    meta = dict(alias=alias)
    scale = (
        sensor.get_data_scale_display()
        if sensor.data_scale != sensor.SCALE_UNITS
        else None
    ) or ''
    uom = (
        sensor.unit_of_measurement
        if sensor.unit_of_measurement != sensor.UNIT_OTHER
        else None
    ) or ''
    meta['unit'] = scale + uom
    return meta


META_LOOKUPS = (
    # Various counter type values
    (
        re.compile(r'\.ports\.(?P<ifname>[^\.]+)\.(?P<counter>[^\.,\)]+)$'),
        dict(alias='{ifname} {counter}'),
    ),
    (
        re.compile(r'\.if[^.()]+Octets(IPv6)?$'),
        dict(
            transform="scaleToSeconds(nonNegativeDerivative(scale({id},8)),1)",
            unit="bits/s",
        ),
    ),
    (
        re.compile(r'\.if(In|Out)Errors$'),
        dict(
            transform="scaleToSeconds(nonNegativeDerivative({id}),1)", unit="errors/s"
        ),
    ),
    (
        re.compile(r'\.if(In|Out)[^\.]*(Pkts|Discards)$'),
        dict(
            transform="scaleToSeconds(nonNegativeDerivative({id}),1)", unit="packets/s"
        ),
    ),
    (
        re.compile(r'\.sysuptime$'),
        dict(transform="scale({id},%.20f)" % (1.0 / TIMETICKS_IN_DAY), unit="days"),
    ),
    (re.compile(r'\.sensors\.'), get_sensor_meta),
    (re.compile(r'\.loadavg[0-9]+min$'), dict(unit="%")),
    (re.compile(r'_percent$'), dict(unit="%")),
    # Memory
    (
        re.compile(r'devices\.(?P<sysname>[^_]+)[^.]+\.memory\..*\.used$'),
        dict(
            unit="bytes", yUnitSystem="binary", title="Used memory", alias="{sysname}"
        ),
    ),
    (
        re.compile(r'devices\.(?P<sysname>[^_]+)[^.]+\.memory\..*\.free$'),
        dict(
            unit="bytes", yUnitSystem="binary", title="Free memory", alias="{sysname}"
        ),
    ),
    (re.compile(r'\.(roundTripTime|responseTime)$'), dict(unit="seconds")),
    (
        re.compile(r'devices\.(?P<sysname>[^_]+)[^.]+\.ping\.roundTripTime$'),
        dict(alias="{sysname}", title="Ping packet round trip time"),
    ),
    (
        re.compile(r'devices\.(?P<sysname>[^_]+)[^.]+\.ping\.packetLoss$'),
        dict(alias="{sysname}", title="Ping packet loss", unit="packets"),
    ),
    # Sysuptime
    (
        re.compile(r'devices\.(?P<sysname>[^_]+)[^.]+\..*\.sysuptime$'),
        dict(alias="{sysname}", title="Uptime", unit="days"),
    ),
    (re.compile(r'\.ipdevpoll\..*\.runtime$'), dict(transform="keepLastValue({id})")),
)


class Graph(object):
    """Builds a Graphite render URL for a graph.

    Instances of this class can be manipulated to produce the desired graph,
    whereas the URL to the currently represented graph can be retrieved by
    coercing the instances to a string or unicode object.

    """

    def __init__(
        self,
        title='',
        width=480,
        height=250,
        targets=None,
        magic_targets=None,
        **kwargs,
    ):
        self.args = dict(template='nav', width=width, height=height)
        self.args.update(kwargs)
        if title:
            self.args['title'] = title

        if targets:
            for target in targets:
                self.add_target(target)

        if magic_targets:
            for target in magic_targets:
                self.add_magic_target(target)

    def __str__(self):
        return reverse("graphite-render") + "?" + urlencode(self.args, True)

    def __repr__(self):
        return '<{cls} {args!r}>'.format(cls=self.__class__.__name__, args=self.args)

    def set_timeframe(self, timeframe):
        """Sets the graph timeframe in terms relative to the current time.

        :param timeframe: An interval that matches Graphite syntax,
                          e.g. '1min', '1day', '24h'. The Graph's 'from'
                          argument will be set to a negative version of this,
                          while the graph's 'until' argument will be set to
                          'now'.
        :type timeframe: basestring
        """
        self.args['from'] = '-%s' % timeframe
        self.args['until'] = 'now'

    def add_target(self, target):
        """Adds a raw target to the graph"""
        self.args.setdefault('target', []).append(target)

    def add_magic_target(self, target):
        """
        Adds a target to the graph, but uses the magic lookups in
        META_LOOKUPS to possibly transform the target using Graphite
        functions and to possibly change some parameters of the graph itself.

        :type target: basestrng
        :returns: The (possibly) modified target.

        """
        meta = get_metric_meta(target)
        target = meta['target']
        if meta['alias']:
            # turns out graphite-web cannot handle non-ascii characters in
            # aliases. we replace them here so we at least get a graph.
            #
            # https://github.com/graphite-project/graphite-web/issues/238
            # https://github.com/graphite-project/graphite-web/pull/480
            alias = meta['alias'].encode('ascii', 'replace').decode("ascii")
            target = 'alias({target}, "{alias}")'.format(target=target, alias=alias)

        self.args.setdefault('target', []).append(target)
        if meta['unit']:
            self.args['vtitle'] = meta['unit']
        if meta['yUnitSystem']:
            self.args['yUnitSystem'] = meta['yUnitSystem']
        if 'title' in meta:
            self.args['title'] = meta['title']

        return target


def get_simple_graph_url(
    metric_paths,
    time_frame="1day",
    title=None,
    width=480,
    height=250,
    magic=True,
    **kwargs,
):
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
    :param magic: Use magic targets
    :return: The URL that will generate the requested graph.

    """
    if isinstance(metric_paths, str):
        metric_paths = [metric_paths]

    target_spec = (
        {'magic_targets': metric_paths} if magic else {'targets': metric_paths}
    )
    graph = Graph(title=title, width=width, height=height, **target_spec)
    graph.set_timeframe(time_frame)

    if kwargs:
        graph.args.update(kwargs)

    return str(graph)


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
    result = dict(
        id=metric_path,
        transform=None,
        target=metric_path,
        unit=None,
        description=None,
        alias=None,
        yUnitSystem=None,
    )
    for pattern, meta in META_LOOKUPS:
        match = pattern.search(metric_path)
        if match:
            result.update(match.groupdict())
            if callable(meta):
                meta = meta(metric_path)
            result.update(meta)

    if result['transform']:
        result['target'] = result['transform'].format(**result)
    if result['alias']:
        result['alias'] = result['alias'].format(**result)
    return result


def extract_series_name(series):
    """
    Extracts a series name from a graphite target expression,
    wildcards included verbatim.

    This is best-effort and is by no means 100% accurate.

    """
    inwild = False
    buffer = ""

    def bufferok(buffer):
        return len(buffer) > 3 and '.' in buffer

    for tok in TARGET_TOKENS.finditer(series):
        tok = tok.group()
        if tok == '(':
            buffer = ""
        elif tok == ')':
            if bufferok(buffer):
                return buffer
            else:
                buffer = ""
        elif tok in ('{', '['):
            inwild = True
            buffer += tok
        elif tok == ',':
            if inwild:
                buffer += tok
            elif bufferok(buffer):
                return buffer
            else:
                buffer = ""
        elif tok in ('}', ']'):
            inwild = False
            buffer += tok
        else:
            buffer += tok
    return buffer if bufferok(buffer) else series


def translate_serieslist_to_regex(series):
    """Translates a Graphite seriesList expression into a regexp pattern"""

    def _convert_char(char):
        if char == '*':
            return r'[^\.]*'
        if char == '?':
            return '.'
        elif char == '.':
            return r'\.'
        elif char == '{':
            return '('
        elif char == '}':
            return ')'
        elif char == ',':
            return '|'
        else:
            return char

    pat = "".join(_convert_char(c) for c in series)
    return re.compile(pat)


def aliased_series(series_list: str, name: str, **meta: str) -> str:
    """
    Add a name to the supplied series_list.
    https://graphite.readthedocs.io/en/latest/functions.html#graphite.render.functions.alias

    Supported keyword arguments:
    :param color: the css color of the graph
    :param renderer: Rickshaw graph renderer to use; one of "area", "stack",
                     "bar", "line", or "scatterplot"
    """
    tmpl = "alias({series_list}, '{name}')"
    if len(meta) > 0:
        # note how key-value pairs from the meta-dict is added in a quite
        # special way to the resulting name; NAV's custom JavaScript Rickshaw
        # graph constructor reconstructs the meta-dict and strips it away from
        # the resulting name before it is displayed. It then uses the meta-dict
        # to customize the graph, such as adding a specific color attribute
        name = ";;".join(f"{key}={val}" for key, val in meta.items()) + ";;" + name
    return tmpl.format(series_list=series_list, name=name)


def summed_series(*series_list: str) -> str:
    """
    Sum each series in all supplied series_lists and return as a single series_list.
    https://graphite.readthedocs.io/en/latest/functions.html#graphite.render.functions.sumSeries
    """
    tmpl = "sumSeries({series_lists})"
    return tmpl.format(series_lists=",".join(series_list))


def nonempty_series(series_list: str, x_files_factor: float = 0.0) -> str:
    """
    Out of all metrics in series_list, draw only the metrics with not
    empty data.

    (A rule of thumb is to use this function if you're dealing with transient
    metrics, so that they only will be shown in the requested timeframes where
    they matter.)

    https://graphite.readthedocs.io/en/latest/functions.html#graphite.render.functions.removeEmptySeries
    """
    tmpl = "removeEmptySeries({series_list}, {x_files_factor})"
    return tmpl.format(series_list=series_list, x_files_factor=x_files_factor)


def json_graph_url(*series_list: str, title: str) -> str:
    """
    Create a url for fetching the JSON data necessary to graph the supplied
    series_lists.
    """
    return get_simple_graph_url(series_list, format="json", title=title)

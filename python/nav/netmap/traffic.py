#
# Copyright (C) 2012, 2013 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Functions for attaching traffic metadata to netmap"""

import logging
from collections import defaultdict

from nav.metrics.data import get_metric_average
from nav.metrics.graphs import get_metric_meta
from nav.metrics.templates import metric_path_for_interface
from nav.models.manage import Interface
from nav.util import chunks
from nav.web.netmap.common import get_traffic_rgb, get_traffic_load_in_percent

TRAFFIC_TIMEPERIOD = '-15min'
INOCTETS = 'ifInOctets'
OUTOCTETS = 'ifOutOctets'
MAX_TARGETS_PER_REQUEST = 500

_logger = logging.getLogger(__name__)


class InterfaceLoad(object):
    """Represents link load for an Interface"""

    def __init__(self, in_bps, out_bps, link_speed):
        self.in_bps = in_bps
        self.out_bps = out_bps
        self.link_speed = link_speed

        self.load_in_percent = get_traffic_load_in_percent(in_bps, link_speed)
        self.rgb = get_traffic_rgb(self.load_in_percent)
        if self.load_in_percent is not None:
            self.formatted_load_in_percent = "{0:.2f}".format(self.load_in_percent)
        else:
            self.formatted_load_in_percent = None

    def __repr__(self):
        return (
            "<InterfaceLoad in_bps={0!r} out_bps={1!r} load_in_percent={2!r} css={3!r}>"
        ).format(self.in_bps, self.out_bps, self.load_in_percent, self.rgb)

    def reversed(self):
        """Returns a copy of this InterfaceLoad for the reverse direction"""
        return InterfaceLoad(self.out_bps, self.in_bps, self.link_speed)

    def to_json(self):
        return {
            'css': self.rgb,
            'in_bps': self.in_bps,
            'out_bps': self.out_bps,
            'percent_by_speed': self.formatted_load_in_percent,
            'load_in_percent': self.load_in_percent,
        }


class Traffic(object):
    """Represents traffic for a given edge from source to target"""

    def __init__(self):
        self.source = None
        self.target = None

    def __repr__(self):
        return "<Traffic source={0!r} target={1!r}>".format(self.source, self.target)

    def to_json(self):
        """to_json presentation for given Traffic in an edge"""
        return {
            'source': self.source and self.source.to_json() or None,
            'target': self.target and self.target.to_json() or None,
        }


def get_traffic_for(interfaces):
    """Get traffic average for the given interfaces using one request

    :param QueryDict interfaces: interfaces to fetch data for
    :returns: A dict of {interface: { suffix: value, suffix: value}}
    """
    metric_mapping = {}  # Store metric_name -> interface
    metrics = []
    traffic = defaultdict(dict)

    _logger.debug("preparing to get traffic data for %d interfaces", len(interfaces))

    # assume transform is the same for all octet counters
    transform = get_metric_meta("." + INOCTETS)["transform"]

    for interface in interfaces:
        # what we need
        ifc_metrics = _get_traffic_counter_metrics_for(interface)
        metrics.extend(ifc_metrics)
        # what to look for in the response
        transformed = [transform.format(id=m) for m in ifc_metrics]
        metric_mapping.update({target: interface for target in transformed})

    targets = [transform.format(id=m) for m in _merge_metrics(sorted(metrics))]

    _logger.debug(
        "getting data for %d targets in chunks of %d",
        len(targets),
        MAX_TARGETS_PER_REQUEST,
    )

    data = {}
    for request in chunks(targets, MAX_TARGETS_PER_REQUEST):
        data.update(get_metric_average(request, start=TRAFFIC_TIMEPERIOD))

    _logger.debug("received %d metrics in response", len(data))

    for metric, value in data.items():
        interface = metric_mapping[metric]
        if INOCTETS in metric:
            traffic[interface].update({INOCTETS: value})
        elif OUTOCTETS in metric:
            traffic[interface].update({OUTOCTETS: value})

    return traffic


def _get_traffic_counter_metrics_for(interface):
    return [
        metric_path_for_interface(interface.netbox, interface.ifname, counter)
        for counter in (INOCTETS, OUTOCTETS)
    ]


def _merge_metrics(metrics):
    """Merge a pre-sorted list of metrics using Graphite wildcard expressions, to
    enable the smallest possible list of targets to ask for in a single request.
    """
    current_prefix = None
    interfaces = set()

    for metric, remaining in zip(metrics, reversed(range(len(metrics)))):
        items = metric.split(".")
        prefix = items[:-2]
        if current_prefix is None:
            current_prefix = prefix

        if prefix == current_prefix:
            interface = items[-2]
            interfaces.add(interface)
        if prefix != current_prefix or remaining == 0:
            emit = "%s.{%s}.{%s}" % (
                ".".join(current_prefix),
                ",".join(interfaces),
                ",".join((INOCTETS, OUTOCTETS)),
            )
            current_prefix = prefix
            interfaces.clear()
            yield emit


def get_traffic_data(port_pair, cache=None):
    """Gets a Traffic instance for the link described by the port pair.

    :param port_pair: tuple containing (source, target)
    :type port_pair: tuple(Interface, Interface)
    :returns: A Traffic instance.
    """
    traffic = Traffic()
    source_port, target_port = port_pair

    traffic.source = _fetch_data(source_port, cache)
    if None in (traffic.source.in_bps, traffic.source.out_bps):
        traffic.target = _fetch_data(target_port, cache)
        traffic.source = traffic.target.reversed()
    else:
        traffic.target = traffic.source.reversed()

    return traffic


def _fetch_data(interface, cache=None):
    in_bps = out_bps = speed = None
    if isinstance(interface, Interface):
        speed = interface.speed
        if cache is not None:
            interface_data = cache[interface]
            if interface_data:
                in_bps = interface_data.get(INOCTETS)
                out_bps = interface_data.get(OUTOCTETS)
        else:
            in_bps, out_bps = get_interface_data(interface)

    return InterfaceLoad(in_bps, out_bps, speed)


def get_interface_data(interface):
    """Get ifin/outoctets for an interface using a single request"""
    _logger.debug("getting traffic data for single interface %r", interface)
    data = get_traffic_for([interface])[interface]
    in_bps, out_bps = data.get(INOCTETS), data.get(OUTOCTETS)
    return in_bps, out_bps

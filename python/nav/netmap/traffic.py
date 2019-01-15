#
# Copyright (C) 2012, 2013 Uninett AS
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

from django.utils.six import iteritems

from nav.metrics.data import get_metric_average
from nav.metrics.graphs import get_metric_meta
from nav.metrics.templates import metric_path_for_interface
from nav.models.manage import Interface
from nav.web.netmap.common import get_traffic_rgb, get_traffic_load_in_percent

TRAFFIC_TIMEPERIOD = '-15min'
INOCTETS = 'ifInOctets'
OUTOCTETS = 'ifOutOctets'

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
            self.formatted_load_in_percent = "{0:.2f}".format(
                self.load_in_percent)
        else:
            self.formatted_load_in_percent = None

    def __repr__(self):
        return (
            "<InterfaceLoad in_bps={0!r} out_bps={1!r} load_in_percent={2!r} "
            "css={3!r}>"
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
        return "<Traffic source={0!r} target={1!r}>".format(
            self.source, self.target)

    def to_json(self):
        """to_json presentation for given Traffic in an edge"""
        return {
            'source': self.source and self.source.to_json() or None,
            'target': self.target and self.target.to_json() or None
        }


def get_traffic_for(interfaces):
    """Get traffic average for the given interfaces using one request

    :param QueryDict interfaces: interfaces to fetch data for
    :returns: A dict of {interface: { suffix: value, suffix: value}}
    """
    metric_mapping = {}  # Store metric_name -> interface
    targets = []
    traffic = defaultdict(dict)
    for interface in interfaces:
        metrics = [m for m in interface.get_port_metrics()
                   if m['suffix'] in [INOCTETS, OUTOCTETS]]
        for metric in metrics:
            target = get_metric_meta(metric['id'])['target']
            metric_mapping[target] = interface
            targets.append(target)

    data = get_metric_average(sorted(targets), start=TRAFFIC_TIMEPERIOD)
    for metric, value in iteritems(data):
        interface = metric_mapping[metric]
        if INOCTETS in metric:
            traffic[interface].update({INOCTETS: value})
        elif OUTOCTETS:
            traffic[interface].update({OUTOCTETS: value})

    return traffic


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
        if cache:
            interface_data = cache[interface]
            if interface_data:
                in_bps = interface_data.get(INOCTETS)
                out_bps = interface_data.get(OUTOCTETS)
        else:
            in_bps, out_bps = get_interface_data(interface)

    return InterfaceLoad(in_bps, out_bps, speed)


def get_interface_data(interface):
    """Get ifin/outoctets for an interface using a single request"""
    in_bps = out_bps = None
    targets = [metric_path_for_interface(interface.netbox.sysname,
                                         interface.ifname, counter)
               for counter in (INOCTETS, OUTOCTETS)]
    targets = [get_metric_meta(t)['target'] for t in targets]
    data = get_metric_average(targets, start=TRAFFIC_TIMEPERIOD)
    for key, value in iteritems(data):
        if 'ifInOctets' in key:
            in_bps = value
        elif 'ifOutOctets' in key:
            out_bps = value
    return in_bps, out_bps

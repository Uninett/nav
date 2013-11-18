#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
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
"""Provides reverse lookups for metrics"""

from nav.models.manage import Netbox, Prefix
from nav.metrics.templates import (metric_prefix_for_device,
                                   metric_prefix_for_interface,
                                   metric_prefix_for_prefix)


def metric_reverse(metrics):
    """Does a reverse on the metric to find relevant database objects"""
    device = 'nav.devices.'
    prefix = 'nav.prefixes.'

    # Check main branch
    if metric.startswith(device):
        return device_reverse(metric)
    elif metric.startswith(prefix):
        return prefix_reverse(metric)


def device_reverse(metrics):
    """Tries to reverse metric to a netbox object"""
    return get_reverses(get_device_lookups(), metrics)


def prefix_reverse(metrics):
    """Tries to reverse metric to a prefix object"""
    return get_reverses(get_prefix_lookups(), metrics)


def interface_reverse(metrics):
    """Tries to reverse metric to an interface object"""
    reverses = device_reverse(metrics)
    if reverses:
        netboxes = reverses.values()
        return get_reverses(get_interface_lookups(netboxes), metrics, 5)


def get_device_lookups():
    """Creates lookups for devices"""
    netboxes = Netbox.objects.all()
    lookups = {}
    for netbox in netboxes:
        lookups[metric_prefix_for_device(netbox.sysname)] = netbox
    return lookups


def get_prefix_lookups():
    """Creates lookups for prefixes"""
    prefixes = Prefix.objects.all()
    lookups = {}
    for prefix in prefixes:
        lookups[metric_prefix_for_prefix(prefix.net_address)] = prefix
    return lookups


def get_interface_lookups(netboxes):
    """Creates lookups for interfaces"""
    lookups = {}
    for netbox in netboxes:
        for interface in netbox.interface_set.all():
            key = metric_prefix_for_interface(netbox.sysname, interface.ifname)
            lookups[key] = interface
    return lookups


def shorten(metric, num):
    """Shortens the prefix to the num first parts"""
    return ".".join(metric.split('.')[:num])


def get_reverses(lookups, metrics, metric_index=3):
    """Returns a dict of metric - object mappings for the given metrics

    :param lookups: Dict of metric -> object mappings
    :param metrics: List of metrics to map to objects
    :param metric_index: number of metric parts we use to look up
                              1     2       3      4     5
                         3 = nav.devices.sysname
                         5 = nav.devices.sysname.ports.ifname
    """
    results = {}
    for metric in metrics:
        metric_prefix = shorten(metric, metric_index)
        result = None
        if metric_prefix in lookups:
            result = lookups[metric_prefix]
        results[metric] = result
    return results



#
# Copyright (C) 2012 Uninett AS
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
"""common helper methods for netmap"""

from nav.models.manage import Netbox
from nav.topology import vlan

STATUS_IMAGE_MAP = {
    Netbox.UP_DOWN: 'red.png',
    Netbox.UP_UP: 'green.png',
    Netbox.UP_SHADOW: 'yellow.png',
}

TRAFFIC_META = {
    'tib': 1099511627776,
    'gib': 1073741824,
    'mib': 1048576,
    'kib': 1024,
    'tb': 1000000000000,
    'gb': 1000000000,
    'mb': 1000000,
    'kb': 1000,
}


def convert_bits_to_si(bits):
    """SI Units, http://en.wikipedia.org/wiki/SI_prefix"""
    if bits >= TRAFFIC_META['tb']:
        return '%.2fTbps' % (bits / TRAFFIC_META['tb'])
    elif bits >= TRAFFIC_META['gb']:
        return '%.2fGbps' % (bits / TRAFFIC_META['gb'])
    elif bits >= TRAFFIC_META['mb']:
        return '%.2fMbps' % (bits / TRAFFIC_META['mb'])
    elif bits >= TRAFFIC_META['kb']:
        return '%.2fKbps' % (bits / TRAFFIC_META['kb'])
    return '%.2fbps' % bits


def convert_bits_to_ieee1541():
    """IEEE 1541, not implemented yet"""
    return None


MEGABIT = 1e6


def get_traffic_load_in_percent(bps, capacity=None):
    """Calculates the load percentage of a link.

    :param bps: bits per second
    :param capacity: capacity on link in Mbps. (ie 1Gbit = 1000 mbps)
    :returns: A
    """
    if not capacity or not bps:
        return None

    traffic_in_percent = (bps / (capacity * MEGABIT)) * 100.0

    if traffic_in_percent > 100 or traffic_in_percent < 0:
        traffic_in_percent = 100.0  # something is odd here
    return traffic_in_percent


def get_traffic_rgb(percent):
    """Traffic load color
    Returns a RGB-triplet for given load percent starting from green to red.
    Grey color returned when we receive no percent.

    :param percent load in procent [0..100]
    """
    if percent is None:
        return 211, 211, 211

    # range(42,236) = 194 steps with nice colors from traffic_gradient_map()
    step_constant = 194.00 / 100.00

    color_map_index = int(percent * step_constant)
    if color_map_index >= 194:
        color_map_index = 193

    rgb = traffic_gradient_map()[color_map_index]

    return int(rgb[0]), int(rgb[1]), int(rgb[2])


GRADIENT_MAP_INTENSITY = 2.0


def traffic_gradient_map():
    """Traffic load gradient map from green, yellow and red."""

    data = []
    for i in reversed(range(42, 236)):
        data.append(
            _traffic_gradient(GRADIENT_MAP_INTENSITY * (i - 236.0) / (42.0 - 237))
        )
    return data


def _traffic_gradient(intensity):
    """
    A beautiful gradient to show traffic load.
    Based on nettkart.pl in TG tech:server goodiebag ^^
    public domain from ftp.gathering.org

    0 = green
    1 = yellow
    2 = red
    3 = white
    4 = black
    """
    gamma = float(1.0 / 1.90)
    if intensity > 3.0:
        return (
            255 * ((4.0 - intensity) ** gamma),
            255 * ((4.0 - intensity) ** gamma),
            255 * ((4.0 - intensity) ** gamma),
        )
    elif intensity > 2.0:
        return (
            255,
            255 * ((intensity - 2.0) ** gamma),
            255 * ((intensity - 2.0) ** gamma),
        )
    elif intensity > 1.0:
        return (255, 255 * ((2.0 - intensity) ** gamma), 0)
    else:
        return (255 * (intensity**gamma), 255, 0)


def get_status_image_link(status):
    """uplink icon for status"""
    try:
        return STATUS_IMAGE_MAP[status]
    except KeyError:
        return STATUS_IMAGE_MAP[Netbox.UP_DOWN]


# Functions required for old netmap, remove when new map is in production
# and old one isn't required anylonger.
def layer2_graph():
    """Layer2 graph"""
    graph = vlan.build_layer2_graph()

    netboxes = graph.nodes()

    connections = []

    for node, neighbours_dict in graph.adjacency_iter():
        for neighbour, keydict in neighbours_dict.items():
            for key, _ in keydict.items():
                # [from_netbox, to_netbox, to_interface]
                connections.append([node, neighbour, key])

    return netboxes, connections

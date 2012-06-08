"""common helper methods for netmap"""
# Copyright (C) 2012 UNINETT AS
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
from django.core.files.storage import FileSystemStorage
from nav.models.manage import Netbox
from nav.topology import vlan
import rrdtool

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

    return (netboxes, connections)


def node_to_json(node, metadata=None):
    """Filter our metadata for a node in JSON-format

    Used for showing metadata in NetMap with D3

    :param node A Netbox model
    :returns: metadata for a node
    """


    last_updated = node.last_updated()
    if last_updated:
        last_updated = last_updated.strftime("%Y-%m-%d %H:%M:%S")
    else:
        last_updated = 'not available'

    position = {'x': metadata.x, 'y': metadata.y} if metadata else None




    return {
        'id': str(node.pk),
        'sysname': str(node.sysname),
        'ip': node.ip,
        'category': str(node.category_id),
        'type': str(node.type),
        'room': str(node.room),
        'up': str(node.up),
        'up_image': get_status_image_link(node.up),
        'ipdevinfo_link': node.get_absolute_url(),
        'last_updated': last_updated,
        'position': position
        }

STATUS_IMAGE_MAP = {
    Netbox.UP_DOWN: 'red.png',
    Netbox.UP_UP: 'green.png',
    Netbox.UP_SHADOW: 'yellow.png',
    }

# todo what happens if an edge has multiple interface links?  ie port-channel
def edge_fetch_uplink(netbox_from, netbox_to):
    """ find uplink(s?) between the two given nodes
        :param netbox_from from node
        :param netbox_to to node
    """
    def uplinks(uplinks, uplink_node):
        """ helper method for finding right uplink to uplink_node """
        interface_link = None
        if uplinks:
            for uplink in uplinks:
                if uplink['other']:
                    if uplink['other'].netbox == uplink_node:
                        interface_link = {'other': uplink['other'],
                                          'thiss': uplink['this']}
                        break
        return interface_link

    interface_link = uplinks(netbox_from.get_uplinks_regarding_of_vlan(),
        netbox_to)

    if not interface_link:
        # try to fetch uplink from opposite side. (graph is undirected,
        # so might be that the edge is drawn from UPLINK to DOWNLINK.
        interface_link = uplinks(netbox_to.get_uplinks_regarding_of_vlan(),
            netbox_from)

    return interface_link

TRAFFIC_META = {
    'tib': 1099511627776,
    'gib': 1073741824,
    'mib': 1048576,
    'kib': 1024,
    'tb': 1000000000000,
    'gb': 1000000000,
    'mb': 1000000,
    'kb': 1000
} # pylint: disable=C0103

def convert_bits_to_si(bits):
    """ SI Units, http://en.wikipedia.org/wiki/SI_prefix
    """
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


def _rrd_info(source):
    """ fetches traffic data from rrd"""
    # Check if RRD file exists , rrdviewer/views.py , refactor.
    filesystem = FileSystemStorage(location=source.rrd_file.path)
    if filesystem.exists(source.rrd_file.get_file_path()):
        try:
            data = rrdtool.fetch(str(source.rrd_file.get_file_path()), 'AVERAGE'
                , '-s -15min')
            # should ask -1 , high probability for None,
            # need to get -2 anyway.
            # -2 is last and most fresh entry of averages in the last 15minutes.
            # (assuming 5min entry points)
            data = data[2][-2][data[1].index(
                source.name)]
            return {'name': source.name, 'description': source.description,
                    'raw': data}
        except:
            # pylint: disable=W0702
            return {'name': source.name, 'description': source.description,
                    'raw': None}

    return {'name': source.name, 'description': source.description, 'raw': None}


def edge_to_json(netbox_from, netbox_to):
    """converts edge information to json"""
    link_speed = None
    tip_inspect_link = False

    # fetch uplinks
    interface_link = edge_fetch_uplink(netbox_from, netbox_to)

    inspect = 'thiss'

    if interface_link:
        if interface_link['thiss'] and interface_link['other'] and\
           interface_link['thiss'].speed != interface_link['other'].speed:
            tip_inspect_link = True
            link_speed = "Not same on both sides!"
        else:
            if interface_link['thiss']:
                link_speed = interface_link['thiss'].speed
            else:
                link_speed = interface_link['other'].speed
                inspect = 'other'

    traffic = {}
    # , u'ifInErrors', u'ifInUcastPkts', u'ifOutErrors', u'ifOutUcastPkts'
    valid_traffic_sources = (
        u'ifHCInOctets', u'ifHCOutOctets', u'ifInOctets', u'ifOutOctets')
    if interface_link:
        for rrd_source in interface_link[inspect].get_rrd_data_sources():
            if rrd_source.description in valid_traffic_sources and\
               rrd_source.description not in traffic:
                traffic[rrd_source.description] = _rrd_info(rrd_source)

    traffic['inOctets'] = None
    traffic['outOctets'] = None

    if 'ifHCInOctets' in traffic:
        traffic['inOctets'] = traffic['ifHCInOctets']
        traffic['outOctets'] = traffic['ifHCOutOctets']
    elif 'ifInOctets' in traffic:
        traffic['inOctets'] = traffic['ifInOctets']
        traffic['outOctets'] = traffic['ifOutOctets']

    traffic['inOctets_css'] = get_traffic_rgb(traffic['inOctets']['raw'],
        link_speed) if traffic['inOctets'] and traffic['inOctets'][
                                               'raw'] else 'N/A'
    traffic['outOctets_css'] = get_traffic_rgb(traffic['outOctets']['raw'],
        link_speed) if traffic['outOctets'] and traffic['inOctets'][
                                                'raw'] else 'N/A'

    # jsonify
    if not interface_link:
        interface_link = 'null' # found no uplinks, json null.
    else:
        interface_link['thiss'] = str(interface_link['thiss'].ifname) + ' at '\
        + str(interface_link['thiss'].netbox.sysname) if interface_link[
                                                         'thiss'] else 'N/A'

        interface_link['other'] = str(interface_link['other'].ifname) + ' at '\
        + str(interface_link['other'].netbox.sysname) if interface_link[
                                                         'other'] else 'N/A'

    return {
        'uplink': interface_link,
        'link_speed': link_speed,
        'tip_inspect_link': tip_inspect_link,
        'traffic': traffic,
        }


def get_traffic_rgb(octets, capacity):
    """Traffic load color

     :param traffic: octets pr second (bytes a second)
     :param capacity: capacity on link in mbps. (ie 1Gbit = 1000 mbps)
    """
    MEGABITS_TO_BITS = 1000000

    avrage_traffic = (float(octets) * 8)  # from octets (bytes) to bits

    traffic_in_percent = avrage_traffic / (capacity * MEGABITS_TO_BITS)

    if traffic_in_percent > 100 or traffic_in_percent < 0:
        traffic_in_percent = 100 # set to red, this indicates something is odd

    # range(42,236) = 194 steps with nice colors from traffic_gradient_map()
    step_constant = 194.00 / 100.00

    color_map_index = int(traffic_in_percent * step_constant)
    if color_map_index >= 194:
        color_map_index = 193

    rgb = traffic_gradient_map()[color_map_index]

    return int(rgb[0]), int(rgb[1]), int(rgb[2])

GRADIENT_MAP_INTENSITY = 2.0

def traffic_gradient_map():
    """Traffic load gradient map from green, yellow and red."""

    data = []
    for i in reversed(range(42, 236)):
        data.append(_traffic_gradient(
            GRADIENT_MAP_INTENSITY * (i - 236.0) / (42.0 - 237)))
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
    if (intensity > 3.0):
        return (
            255 * ((4.0 - intensity) ** gamma),
            255 * ((4.0 - intensity) ** gamma),
            255 * ((4.0 - intensity) ** gamma))
    elif (intensity > 2.0):
        return (255, 255 * ((intensity - 2.0) ** gamma),
                255 * ((intensity - 2.0) ** gamma))
    elif (intensity > 1.0):
        return (255, 255 * ((2.0 - intensity) ** gamma), 0)
    else:
        return (255 * (intensity ** gamma), 255, 0)


def get_status_image_link(status):
    """ uplink icon for status
    """
    try:
        return STATUS_IMAGE_MAP[status]
    except:
        # pylint: disable=W0702
        return STATUS_IMAGE_MAP[Netbox.UP_DOWN]

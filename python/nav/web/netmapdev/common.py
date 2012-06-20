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
from django.core.urlresolvers import reverse
import networkx as nx
from nav.models.manage import Netbox
from nav.rrd import presenter
from nav.topology import vlan
import rrdtool
import logging

_LOGGER = logging.getLogger(__name__)

# pylint: disable=C0103
def build_netmap_layer2_graph(view=None):
    """
    Builds a netmap layer 2 graph, based on nav's build_layer2_graph method.


    :param view A NetMapView for getting node positions according to saved netmap view.

    :return NetworkX MultiDiGraph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """
    _LOGGER.debug("build_netmap_layer2_graph() start")
    topology_without_metadata = vlan.build_layer2_graph(
        ('to_interface__netbox',))
    _LOGGER.debug("build_netmap_layer2_graph() topology graph done")
    graph = nx.MultiDiGraph()
    # Make a copy of the graph, and add edge meta data
    for n, nbrdict, key in topology_without_metadata.edges_iter(keys=True):
        graph.add_edge(n, nbrdict, key=key,
            metadata=edge_metadata(key.netbox, key, nbrdict, key.to_interface))
    _LOGGER.debug("build_netmap_layer2_graph() graph copy with metadata done")
    if view:
        node_set = view.node_position_set.all()

        for node in graph.nodes(data=True):
            tmp = [x for x in node_set if x.netbox == node[0]]
            if tmp:
                node[1]['metadata'] = tmp[0]
    _LOGGER.debug("build_netmap_layer2_graph() view positions and graph done")
    return graph

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

    position = {'x': metadata.x, 'y': metadata.y} if metadata else None
    return {
            'id': str(node.pk),
            'sysname': str(node.sysname),
            'category': str(node.category_id),
            'ip': node.ip,
            'ipdevinfo_link': reverse('ipdevinfo-details-by-name',
                args=[node.sysname]),
            'position': position,
            'up': str(node.up),
            'up_image': get_status_image_link(node.up),
            }

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

def __rrd_info2(source):
    # todo : what to do if rrd source is not where it should be? Will return 0
    # if it can't find RRD file for example
    a = presenter.Presentation()
    a.add_datasource(source.pk)
    return {'name': source.name, 'description': source.description,
            'raw': a.average()[0]}


def edge_metadata(thiss_netbox, thiss_interface, other_netbox, other_interface):
    """
    :param thiss_netbox This netbox (edge from)
    :param thiss_interface This netbox's interface (edge from)
    :param other_netbox Other netbox (edge_to)
    :param other_interface Other netbox's interface (edge_to)
    """
    error = {}
    tip_inspect_link = False

    uplink = {'thiss': {'netbox': thiss_netbox, 'interface': thiss_interface},
         'other': {'netbox': other_netbox,
                   'interface': other_interface}}

    if thiss_interface and other_interface and thiss_interface.speed != \
                                               other_interface.speed:
        tip_inspect_link = True
        link_speed = None
        error[
        'link_speed'] = 'Interface link speed not the same between the nodes'
    else:
        if thiss_interface:
            link_speed = thiss_interface.speed
        else:
            link_speed = other_interface.speed


    return {
            'uplink': uplink,
            'tip_inspect_link': tip_inspect_link,
            'link_speed': link_speed,
            'error': error,
    }

def edge_to_json(metadata):
    """converts edge information to json"""

    uplink = metadata['uplink']
    link_speed = metadata['link_speed']
    tip_inspect_link = metadata['tip_inspect_link']
    error = metadata['error']

    # jsonify
    if not uplink:
        uplink_json = 'null' # found no uplinks, json null.
    else:
        uplink_json = {}

        if uplink['thiss']['interface']:
            uplink_json.update(
                    {'thiss': {'interface': "{0} at {1}".format(
                    str(uplink['thiss']['interface'].ifname),
                    str(uplink['thiss']['interface'].netbox.sysname)
                ), 'netbox': uplink['thiss']['netbox'].sysname}}
            )
        else: uplink_json.update({'thiss': {'interface': 'N/A', 'netbox': 'N/A'}})

        if uplink['other']['interface']:
            uplink_json.update(
                    {'other': {'interface': "{0} at {1}".format(
                    str(uplink['other']['interface'].ifname),
                    str(uplink['other']['interface'].netbox.sysname)
                ), 'netbox': uplink['other']['netbox'].sysname}}
            )
        else: uplink_json.update({'other': {'interface': 'N/A', 'netbox': 'N/A'}})

    if 'link_speed' in error.keys():
        link_speed = error['link_speed']
    elif not link_speed:
        link_speed = "N/A"

    return {
        'uplink': uplink_json,
        'link_speed': link_speed,
        'tip_inspect_link': tip_inspect_link,
        }


def _get_datasource_lookup(graph):
    edges_iter = graph.edges_iter(data=True)

    interfaces = set()
    for _, _, w in edges_iter:
        w = w['metadata']
        if 'uplink' in w:
            if w['uplink']['thiss']['interface']:
                interfaces.add(w['uplink']['thiss']['interface'].pk)

            if w['uplink']['other']['interface']:
                interfaces.add(w['uplink']['other']['interface'].pk)

    _LOGGER.debug(
        "netmap:attach_rrd_data_to_edges() datasource id filter list done")

    from nav.models.rrd import RrdDataSource

    datasources = RrdDataSource.objects.filter(
        rrd_file__key='interface').select_related('rrd_file').filter(
        rrd_file__value__in=interfaces)
    _LOGGER.debug("netmap:attach_rrd_data_to_edges() Datasources fetched done")

    lookup_dict = {}
    for data in datasources:
        interface = int(data.rrd_file.value)
        if interface in lookup_dict:
            lookup_dict[interface].append(data)
        else:
            lookup_dict.update({interface: [data]})

    _LOGGER.debug(
        "netmap:attach_rrd_data_to_edges() Datasources rearranged in dict")

    return lookup_dict


def attach_rrd_data_to_edges(graph, json=None, debug=False):
    """ called from d3_js to attach rrd_data after it has attached other
    edge metadata by using edge_to_json

    :param graph A network x graph matching d3_js graph format.
    """

    datasource_lookup = _get_datasource_lookup(graph)

    # , u'ifInErrors', u'ifInUcastPkts', u'ifOutErrors', u'ifOutUcastPkts'
    valid_traffic_sources = (
        u'ifHCInOctets', u'ifHCOutOctets', u'ifInOctets', u'ifOutOctets')

    edges_iter = graph.edges_iter(data=True)
    for j, k, w in edges_iter:
        metadata = w['metadata']
        traffic = {}

        if metadata['uplink']['thiss']['interface'].pk in datasource_lookup:
            datasources_for_interface = datasource_lookup[
                                        metadata['uplink']['thiss'][
                                        'interface'].pk]
            for rrd_source in datasources_for_interface:
                if rrd_source.description in valid_traffic_sources and\
                   rrd_source.description not in traffic:
                    if debug:
                        traffic[rrd_source.description] = __rrd_info2(
                            rrd_source)
                    break


        traffic['inOctets'] = None
        traffic['outOctets'] = None

        if 'ifInOctets' in traffic:
            traffic['inOctets'] = traffic['ifInOctets']
        if 'ifOutOctets' in traffic:
            traffic['outOctets'] = traffic['ifOutOctets']

        # Overwrite traffic inOctets and outOctets
        # if 64 bit counters are present
        if 'ifHCInOctets' in traffic:
            traffic['inOctets'] = traffic['ifHCInOctets']

        if 'ifHCOutOctets' in traffic:
            traffic['outOctets'] = traffic['ifHCOutOctets']



        traffic['inOctets_css'] = get_traffic_rgb(traffic['inOctets']['raw'],
            metadata['link_speed']) if traffic['inOctets'] and\
                                       traffic['inOctets']['raw'] else 'N/A'
        traffic['outOctets_css'] = get_traffic_rgb(traffic['outOctets']['raw'],
            metadata['link_speed']) if traffic['outOctets'] and\
                                       traffic['inOctets']['raw'] else 'N/A'


        for json_edge in json:

            if json_edge['source'] == j and json_edge['target'] == k:
                json_edge['data'].update({'traffic':traffic})
                break
    return json

def get_traffic_rgb(octets, capacity=None):
    """Traffic load color
    Red color if capacity is not defined. Normally indicates an error
    ex. link_speed on interfaces between nodes are not equal!

     :param traffic: octets pr second (bytes a second)
     :param capacity: capacity on link in mbps. (ie 1Gbit = 1000 mbps)
    """

    if not capacity:
        return 255, 255, 0

    MEGABITS_TO_BITS = 1000000

    average_traffic = (float(octets) * 8)  # from octets (bytes) to bits

    traffic_in_percent = average_traffic / (capacity * MEGABITS_TO_BITS)

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

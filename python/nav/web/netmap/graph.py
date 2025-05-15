#
# Copyright (C) 2007, 2010, 2011, 2014 Uninett AS
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
"""Graph utility functions for Netmap"""

from datetime import datetime
from collections import defaultdict
import logging

from django.shortcuts import get_object_or_404

from nav.netmap.metadata import (
    node_to_json_layer2,
    edge_to_json_layer2,
    node_to_json_layer3,
    edge_to_json_layer3,
    vlan_to_json,
    get_vlan_lookup_json,
)
from nav.netmap.topology import (
    build_netmap_layer3_graph,
    build_netmap_layer2_graph,
    _get_vlans_map_layer2,
    _get_vlans_map_layer3,
)
from nav.topology import vlan
from nav.models.manage import Interface, Prefix, GwPortPrefix, Location, Room
from nav.netmap.traffic import get_traffic_data, get_traffic_for

from .common import get_traffic_rgb
from .cache import cache_traffic, cache_topology

_logger = logging.getLogger(__name__)


def get_topology_graph(layer=2, load_traffic=False, view=None):
    """Builds and returns topology graph for the given layer"""
    if layer == 2:
        return _json_layer2(load_traffic, view=view)
    else:
        return _json_layer3(load_traffic, view=view)


@cache_topology("layer 2")
def _json_layer2(load_traffic=False, view=None):
    topology_without_metadata = vlan.build_layer2_graph(
        (
            'to_interface__netbox',
            'to_interface__netbox__room',
            'to_netbox__room',
            'netbox__room',
            'to_interface__netbox__room__location',
            'to_netbox__room__location',
            'netbox__room__location',
        )
    )

    vlan_by_interface, vlan_by_netbox = _get_vlans_map_layer2(topology_without_metadata)

    graph = build_netmap_layer2_graph(
        topology_without_metadata, vlan_by_interface, vlan_by_netbox, load_traffic, view
    )

    def get_edge_from_meta(meta):
        edge = meta['metadata'][0]
        return edge.u.netbox, edge.v.netbox

    result = {
        'vlans': get_vlan_lookup_json(vlan_by_interface),
        'nodes': _get_nodes(node_to_json_layer2, graph),
        'links': [
            edge_to_json_layer2(get_edge_from_meta(meta), meta)
            for u, v, meta in graph.edges(data=True)
        ],
    }
    return result


@cache_topology("layer 3")
def _json_layer3(load_traffic=False, view=None):
    topology_without_metadata = vlan.build_layer3_graph(('prefix__vlan__net_type',))

    vlans_map = _get_vlans_map_layer3(topology_without_metadata)

    graph = build_netmap_layer3_graph(topology_without_metadata, load_traffic, view)

    def get_edge_from_meta(meta):
        edges = next(iter(meta['metadata'].values()))
        first = next(iter(edges))
        return first.u.netbox, first.v.netbox

    result = {
        'vlans': [vlan_to_json(prefix.vlan) for prefix in vlans_map],
        'nodes': _get_nodes(node_to_json_layer3, graph),
        'links': [
            edge_to_json_layer3(get_edge_from_meta(meta), meta)
            for u, v, meta in graph.edges(data=True)
        ],
    }
    return result


def _get_nodes(node_to_json_function, graph):
    nodes = {}
    for node, nx_metadata in graph.nodes(data=True):
        nodes.update(node_to_json_function(node, nx_metadata))
    return nodes


def get_traffic_gradient():
    """Builds a dictionary of rgb values from green to red"""
    keys = ('r', 'g', 'b')

    return [dict(zip(keys, get_traffic_rgb(percent))) for percent in range(0, 101)]


@cache_traffic("layer 2")
def get_layer2_traffic(location_or_room_id=None):
    """Fetches traffic data for layer 2"""
    start = datetime.now()

    # TODO: Handle missing?
    if location_or_room_id is None or not location_or_room_id:
        interfaces = Interface.objects.filter(to_netbox__isnull=False).select_related(
            'netbox', 'to_netbox', 'to_interface__netbox'
        )
    else:
        interfaces = Interface.objects.filter(
            to_netbox__isnull=False,
        ).select_related('netbox', 'to_netbox', 'to_interface__netbox')

        try:
            room = Room.objects.get(id=location_or_room_id)
        except Room.DoesNotExist:
            location = Location.objects.get(id=location_or_room_id)
            interfaces = interfaces.filter(netbox__room__location=location)
        else:
            interfaces = interfaces.filter(netbox__room=room)

    edges = defaultdict(set)
    for interface in interfaces:
        edges[(interface.netbox_id, interface.to_netbox_id)].add(interface)

    _logger.debug(
        "Produced %d edges from %d interfaces in %s",
        len(edges),
        len(interfaces),
        datetime.now() - start,
    )

    complete_interface_set = set(interfaces) | set(
        ifc.to_interface for ifc in interfaces if ifc.to_interface
    )
    traffic_cache = get_traffic_for(complete_interface_set)
    _logger.debug('Traffic cache built. Time used so far: %s', datetime.now() - start)

    traffic = []
    for (source, target), edge_interfaces in edges.items():
        edge_traffic = []
        for interface in edge_interfaces:
            to_interface = interface.to_interface
            data = get_traffic_data((interface, to_interface), traffic_cache).to_json()
            data.update(
                {
                    'source_ifname': interface.ifname if interface else '',
                    'target_ifname': to_interface.ifname if to_interface else '',
                }
            )
            edge_traffic.append(data)
        traffic.append(
            {
                'source': source,
                'target': target,
                'edges': edge_traffic,
            }
        )

    _logger.debug('Total time used: %s', datetime.now() - start)
    return traffic


@cache_traffic("layer 3")
def get_layer3_traffic(location_or_room_id=None):
    """Fetches traffic data for layer 3"""

    prefixes = Prefix.objects.filter(
        vlan__net_type__in=('link', 'elink', 'core')
    ).select_related('vlan__net_type')

    # No location/room => fetch data for all nodes
    if location_or_room_id is None or not location_or_room_id:
        router_ports = GwPortPrefix.objects.filter(
            prefix__in=prefixes,
            interface__netbox__category__in=('GW', 'GSW'),  # Or might be faster
        ).select_related(
            'interface',
            'interface__to_interface',
        )
    else:
        # Sanity check: Does the room exist?
        room = Room.objects.filter(id=location_or_room_id)
        if room.exists():
            location = get_object_or_404(Room, id=location_or_room_id)
        else:
            location = get_object_or_404(Location, id=location_or_room_id)

        router_ports = GwPortPrefix.objects.filter(
            prefix__in=prefixes,
            interface__netbox__room__location=location,
            interface__netbox__category__in=('GW', 'GSW'),  # Or might be faster
        ).select_related(
            'interface',
            'interface__to_interface',
        )

    router_ports_prefix_map = defaultdict(list)
    for router_port in router_ports:
        router_ports_prefix_map[router_port.prefix].append(router_port)

    interfaces = set()
    traffic = []

    for prefix in prefixes:
        gwport_prefixes = router_ports_prefix_map[prefix]

        if gwport_prefixes and prefix.vlan.net_type.id != 'elink':
            for gwport_prefix_a in gwport_prefixes:
                for gwport_prefix_b in gwport_prefixes:
                    if gwport_prefix_a is not gwport_prefix_b:
                        interface_a = gwport_prefix_a.interface
                        interface_b = gwport_prefix_b.interface
                        interfaces.add(
                            (
                                interface_a.netbox_id,
                                interface_b.netbox_id,
                                interface_a,
                                interface_b,
                            )
                        )
    for source, target, interface, to_interface in interfaces:
        traffic.append(
            {
                'source': source,
                'target': target,
                'source_ifname': interface.ifname,
                'target_ifname': to_interface.ifname,
                'traffic_data': get_traffic_data(
                    (
                        interface,
                        to_interface,
                    )
                ).to_json(),
            }
        )
    return traffic

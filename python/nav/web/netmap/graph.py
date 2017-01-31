#
# Copyright (C) 2007, 2010, 2011, 2014 UNINETT AS
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
"""Graph utility functions for Netmap"""

from datetime import datetime
from collections import defaultdict

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
from nav.models.manage import Interface, Prefix, GwPortPrefix, Location
from nav.netmap.traffic import get_traffic_data, get_traffic_for
from django.core.cache import cache

from .common import get_traffic_rgb

import logging
_logger = logging.getLogger(__name__)

# TODO: Make adjustable in NAV settings
CACHE_TIMEOUT = 25*60 # 25 minutes
TRAFFIC_CACHE_TIMEOUT = 10*60 # 10 minutes


def get_topology_graph(layer=2, load_traffic=False, view=None):
    """Builds and returns topology graph for the given layer"""
    if layer == 2:
        return _json_layer2(load_traffic, view)
    else:
        return _json_layer3(load_traffic, view)


def _json_layer2(load_traffic=False, view=None):
    cache_key = _cache_key("topology", "layer2")
    cached = cache.get(cache_key)
    # Catch hit
    if cached is not None:
        return cached

    topology_without_metadata = vlan.build_layer2_graph(
        (
            'to_interface__netbox',
            'to_interface__netbox__room',
            'to_netbox__room',
            'netbox__room', 'to_interface__netbox__room__location',
            'to_netbox__room__location',
            'netbox__room__location',
        )
    )

    vlan_by_interface, vlan_by_netbox = _get_vlans_map_layer2(
        topology_without_metadata)

    graph = build_netmap_layer2_graph(topology_without_metadata,
                                      vlan_by_interface, vlan_by_netbox,
                                      load_traffic, view)

    result = {
        'vlans': get_vlan_lookup_json(vlan_by_interface),
        'nodes': _get_nodes(node_to_json_layer2, graph),
        'links': [edge_to_json_layer2((node_a, node_b), nx_metadata) for
                  node_a, node_b, nx_metadata in graph.edges_iter(data=True)]
    }
    # add to cache
    cache.set(cache_key, result, CACHE_TIMEOUT)
    return result


def _json_layer3(load_traffic=False, view=None):
    cache_key = _cache_key("topology", "layer3")
    cached = cache.get(cache_key)
    # Catch hit
    if cached is not None:
        return cached


    topology_without_metadata = vlan.build_layer3_graph(
        ('prefix__vlan__net_type', 'gwportprefix__prefix__vlan__net_type',)
    )

    vlans_map = _get_vlans_map_layer3(topology_without_metadata)

    graph = build_netmap_layer3_graph(topology_without_metadata, load_traffic,
                                      view)
    result = {
        'vlans': [vlan_to_json(prefix.vlan) for prefix in vlans_map],
        'nodes': _get_nodes(node_to_json_layer3, graph),
        'links': [edge_to_json_layer3((node_a, node_b), nx_metadata) for
                  node_a, node_b, nx_metadata in graph.edges_iter(data=True)]
    }
    cache.set(cache_key, result, CACHE_TIMEOUT)
    return result


def _get_nodes(node_to_json_function, graph):
    nodes = {}
    for node, nx_metadata in graph.nodes_iter(data=True):
        nodes.update(node_to_json_function(node, nx_metadata))
    return nodes


def get_traffic_gradient():
    """Builds a dictionary of rgb values from green to red"""
    keys = ('r', 'g', 'b')

    return [
        dict(zip(keys, get_traffic_rgb(percent))) for percent in range(0, 101)
    ]


def get_traffic_interfaces(edges, interfaces):
    """Gives list of edges and interfaces, filter out the interfaces we are to
    fetch traffic for

    :param set edges: a set of edges represented by netbox pairs
    :param QuerySet interfaces: all interfaces
    :returns: The list of interfaces we have to fetch traffic for.
    """
    storage = {}
    for source, target in edges:
        edge_interfaces = interfaces.filter(
            netbox_id=source,
            to_netbox_id=target
        )
        for interface in edge_interfaces:
            storage[interface.pk] = interface
            if interface.to_interface:
                storage[interface.to_interface.pk] = interface.to_interface

    return storage.values()


def get_layer2_traffic(locationId, shouldInvalidate=False):
    """Fetches traffic data for layer 2"""
    # Cache model: Index traffic by location
    cache_key = _cache_key("traffic", "locationId", "layer 2")
    if not shouldInvalidate:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    else:
        cache.delete(cache_key)

    start = datetime.now()

    # Sanity check: Does the room exist?
    location = Location.objects.get(id=locationId)
    # Fetch interfaces for devices in that room
    interfaces = Interface.objects.filter(
        to_netbox__isnull=False,
        netbox__room__location=location
    ).select_related(
        'netbox', 'to_netbox', 'to_interface__netbox'
    )

    edges = set([
        (
            interface.netbox_id,
            interface.to_netbox_id
        )
        for interface in interfaces
    ])

    traffic = []
    traffic_cache = get_traffic_for(
        get_traffic_interfaces(edges, interfaces))

    for source, target in edges:
        edge_interfaces = interfaces.filter(
            netbox_id=source,
            to_netbox_id=target
        )
        edge_traffic = []
        for interface in edge_interfaces:
            to_interface = interface.to_interface
            data = get_traffic_data(
                (interface, to_interface), traffic_cache).to_json()
            data.update({
                'source_ifname': interface.ifname if interface else '',
                'target_ifname': to_interface.ifname if to_interface else ''
            })
            edge_traffic.append(data)
        traffic.append({
            'source': source,
            'target': target,
            'edges': edge_traffic,
        })

    _logger.debug('Time used: %s', datetime.now() - start)
    cache.set(cache_key, traffic, TRAFFIC_CACHE_TIMEOUT)
    return traffic

def get_layer3_traffic(locationId, shouldInvalidate=False):
    """Fetches traffic data for layer 3"""

    # Cache model: Index traffic by location
    cache_key = _cache_key("traffic", "locationId", "layer 3")

    if not shouldInvalidate:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    else:
        cache.delete(cache_key)

    # Sanity check: Does the room exist?
    location = Location.objects.get(id=locationId)

    prefixes = Prefix.objects.filter(
        vlan__net_type__in=('link', 'elink', 'core')
    ).select_related('vlan__net_type')

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

        if gwport_prefixes and prefix.vlan.net_type.id is not 'elink':

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
                                interface_b
                            )
                        )
    for source, target, interface, to_interface in interfaces:
        traffic.append({
            'source': source,
            'target': target,
            'source_ifname': interface.ifname,
            'target_ifname': to_interface.ifname,
            'traffic_data': get_traffic_data(
                (interface, to_interface,)
            ).to_json()
        })

    cache.set(cache_key, traffic, TRAFFIC_CACHE_TIMEOUT)

    return traffic

# TODO: Consider using a proper slug generator for this
def _cache_key(*args):
    """Construct a namespace cache key for storing/retrieving memory-cached data

    :param args: The elements which, when joined, set the index of the data

    Example:

    _cache_key("topology", "layer 3")
    => netmap:topology:layer3

    """
    args = (str(a).replace(' ', '-') for a in args)
    return 'netmap:' + ':'.join(args)

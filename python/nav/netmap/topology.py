#
# Copyright (C) 2012 Uninett AS
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
"""netmap's topology functions"""

from collections import defaultdict
import logging

import networkx as nx

from nav.models.manage import SwPortVlan
from nav.netmap.metadata import edge_metadata_layer3, edge_metadata_layer2
from nav.netmap.traffic import get_traffic_data, Traffic


_logger = logging.getLogger(__name__)


def _get_vlans_map_layer2(graph):
    """Builds two dictionaries to lookup VLAN information for layer2
    :param a networkx NAV topology graph
    :returns a tuple to look up vlans by interface and/or netbox"""
    interface_id_list = [x[2].id for x in graph.edges(keys=True)]

    vlan_by_interface = defaultdict(list)
    vlan_by_netbox = defaultdict(dict)
    for swpv in SwPortVlan.objects.filter(
        interface__in=list(interface_id_list)
    ).select_related():
        vlan_by_interface[swpv.interface].append(swpv)

        # unique storing on internal nav vlan id
        vlan_by_netbox[swpv.interface.netbox].update({swpv.vlan.id: swpv})

    return vlan_by_interface, vlan_by_netbox


def _get_vlans_map_layer3(graph):
    vlans = set()
    for _, _, swpv in graph.edges(keys=True):
        vlans.add(swpv)
    return vlans


def build_netmap_layer2_graph(
    topology_without_metadata,
    vlan_by_interface,
    vlan_by_netbox,
    load_traffic=False,
    view=None,
):
    """
    Builds a netmap layer 2 graph, based on nav's build_layer2_graph method.
    Reduces a topology graph from nav.topology.vlan, but retains it's
     directional (MultiDiGraph) properties as metadata under the key 'metadata'

    This is done as the visualization in Netmap won't ever be drawing multiple
    spines between edges as it will turn into a mess, instead we want to access
    such data as metadata.

    :param topology_without_metadata: nav.topology.vlan.build*_graph networkx
     graph
    :param vlan_by_interface: dictionary to lookup up vlan's attached to given
     interface
    :param vlan_by_netbox: dictonary to lookup up vlan's, keyed by netbox.
    :param view A NetMapView for getting node positions according to saved
     netmap view.
    :type topology_without_metadata: networkx.MultiDiGraph
    :type vlan_by_interface: dict
    :type vlan_by_netbox: dict
    :type view: nav.modeles.profiles.NetmapView
    :return NetworkX Graph with attached metadata for edges and nodes
    """
    _logger.debug("_build_netmap_layer2_graph()")
    netmap_graph = nx.Graph()

    # basically loops over the whole MultiDiGraph from nav.topology and make
    # sure we fetch all 'loose' ends and makes sure they get attached as
    # metadata into netmap_graph
    for source, neighbors_dict in topology_without_metadata.adjacency():
        for target, connected_interfaces_at_source_for_target in neighbors_dict.items():
            for interface in connected_interfaces_at_source_for_target:
                # fetch existing metadata that might have been added already
                existing_metadata = netmap_graph.get_edge_data(source, target) or {}
                port_pairs = existing_metadata.setdefault('port_pairs', set())
                port_pair = frozenset((interface, interface.to_interface))
                if len(port_pair) < 2:
                    _logger.warning("Wonky self-loop at %r", port_pair)
                    continue  # ignore wonk!
                port_pairs.add(port_pair)

                netmap_graph.add_edge(target, source, **existing_metadata)

    _logger.debug(
        "build_netmap_layer2_graph() graph reduced.Port_pair metadata attached"
    )

    empty_traffic = Traffic()
    for source, target, metadata_dict in netmap_graph.edges(data=True):
        for interface_a, interface_b in metadata_dict.get('port_pairs'):
            traffic = (
                get_traffic_data((interface_a, interface_b))
                if load_traffic
                else empty_traffic
            )
            additional_metadata = edge_metadata_layer2(
                (source, target), interface_a, interface_b, vlan_by_interface, traffic
            )

            metadata = metadata_dict.setdefault('metadata', list())
            metadata.append(additional_metadata)

    _logger.debug("build_netmap_layer2_graph() netmap metadata built")

    for node, data in netmap_graph.nodes(data=True):
        if node in vlan_by_netbox:
            data['metadata'] = {
                'vlans': sorted(
                    vlan_by_netbox[node].items(), key=lambda x: x[1].vlan.vlan
                )
            }

    _logger.debug("build_netmap_layer2_graph() vlan metadata for _nodes_ done")

    if view:
        saved_views = view.node_positions.all()
        netmap_graph = _attach_node_positions(netmap_graph, saved_views)
    _logger.debug("build_netmap_layer2_graph() view positions and graph done")

    return netmap_graph


def build_netmap_layer3_graph(topology_without_metadata, load_traffic=False, view=None):
    """
    Builds a netmap layer 3 graph, based on nav's build_layer3_graph method.

    :param load_traffic: set to true for fetching Traffic statistics data
                         for your network topology.
    :param view: A NetMapView for getting node positions according to saved
                 netmap view.
    :type load_traffic: bool
    :type view: nav.models.profiles.NetmapView

    :return NetworkX Graph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """

    # Make a copy of the graph, and add edge meta data
    graph = nx.Graph()
    for gwpp_u, gwpp_v, prefix in topology_without_metadata.edges(keys=True):
        netbox_u = gwpp_u.interface.netbox
        netbox_v = gwpp_v.interface.netbox

        existing_metadata = graph.get_edge_data(netbox_u, netbox_v) or {}
        gwportprefix_pairs = existing_metadata.setdefault('gwportprefix_pairs', set())
        existing_metadata['key'] = prefix.vlan
        gwportprefix = frozenset((gwpp_u, gwpp_v))
        gwportprefix_pairs.add(gwportprefix)

        graph.add_edge(netbox_v, netbox_u, **existing_metadata)

    _logger.debug("build_netmap_layer3_graph() graph copy with metadata done")

    empty_traffic = Traffic()
    for u, v, metadata_dict in graph.edges.data():
        for gwpp_u, gwpp_v in metadata_dict.get('gwportprefix_pairs'):
            traffic = (
                get_traffic_data((gwpp_u.interface, gwpp_v.interface))
                if load_traffic
                else empty_traffic
            )
            additional_metadata = edge_metadata_layer3((u, v), gwpp_u, gwpp_v, traffic)
            assert gwpp_u.prefix.vlan.id == gwpp_v.prefix.vlan.id, (
                "GwPortPrefix must reside inside VLan for given Prefix, bailing!"
            )
            metadata = metadata_dict.setdefault('metadata', defaultdict(list))
            metadata[gwpp_u.prefix.vlan.id].append(additional_metadata)

    if view:
        graph = _attach_node_positions(graph, view.node_positions.all())
    _logger.debug("build_netmap_layer3_graph() view positions and graph done")
    return graph


def _attach_node_positions(graph, node_set):
    """Attaches node positions from a set of nodes which is extracted from a
    given map view earlier in the call stack.

    :param graph graph to modify metadata on
    :param node_set NetmapViewNodePosition collection for a given map view
    """

    # node is a tuple(netbox, networkx_graph_node_meta_dict)
    # Traversing our generated graph which misses node positions..
    for node, metadata in graph.nodes(data=True):
        # Find node metadata in saved map view if it has any.
        node_meta_dict = [x for x in node_set if x.netbox == node]

        # Attached position meta data if map view has meta data on node in graph
        if node_meta_dict:
            if 'metadata' in metadata:
                # has vlan meta data, need to just update position data
                metadata['metadata'].update({'position': node_meta_dict[0]})
            else:
                metadata['metadata'] = {'position': node_meta_dict[0]}
    return graph

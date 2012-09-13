#
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
"""netmap's topology functions"""
import logging
import networkx as nx
from collections import defaultdict
from nav.models.manage import SwPortVlan, Prefix
from nav.netmap.metadata import edge_metadata_layer3, edge_metadata_layer2
from nav.topology import vlan


_LOGGER = logging.getLogger(__name__)


def _get_vlans_map_layer2(graph):
    """Builds two dictionaries to lookup VLAN information for layer2
    :param a networkx NAV topology graph
    :returns a tuple to look up vlans by interface and/or netbox"""
    interface_id_list = list()
    for _, _, key in graph.edges_iter(keys=True):
        if key.vlan:
            interface_id_list.append(key.id)

    vlan_by_interface = defaultdict(list)
    vlan_by_netbox = defaultdict(dict)
    for swpv in SwPortVlan.objects.filter(
        interface__in=list(interface_id_list)).select_related():

        vlan_by_interface[swpv.interface].append(swpv)

        # unique storing on internal nav vlan id
        vlan_by_netbox[swpv.interface.netbox].update({swpv.vlan.id:swpv})

    return (vlan_by_interface, vlan_by_netbox)

def _get_vlans_map_layer3(graph):
    """Builds a dictionary to lookup VLAN (IP broadcast domain) information
     for layer3. See nav.models.manage.Vlan

    :param a networkx NAV topology graph
    :returns a map to lookup prefixes by internal NAV VLAN ID"""

    prefix_list_id = list()
    for _, _, prefix in graph.edges_iter(keys=True):
        prefix_list_id.append(prefix.vlan.id)

    prefixes_by_navvlan = defaultdict(list)
    for prefix_in_navvlan in Prefix.objects.filter(
        vlan__id__in=list(prefix_list_id)).select_related():

        prefixes_by_navvlan[prefix_in_navvlan.vlan.id].append(prefix_in_navvlan)

    return prefixes_by_navvlan

def build_netmap_layer2_graph(view=None):
    """
    Builds a netmap layer 2 graph, based on nav's build_layer2_graph method.


    :param view A NetMapView for getting node positions according to saved
    netmap view.

    :return NetworkX MultiDiGraph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """
    _LOGGER.debug("build_netmap_layer2_graph() start")
    topology_without_metadata = vlan.build_layer2_graph(
        (
        'to_interface__netbox', 'to_interface__netbox__room', 'to_netbox__room',
        'netbox__room', 'to_interface__netbox__room__location',
        'to_netbox__room__location', 'netbox__room__location'))
    _LOGGER.debug("build_netmap_layer2_graph() topology graph done")

    vlan_by_interface, vlan_by_netbox = _get_vlans_map_layer2(
        topology_without_metadata)
    _LOGGER.debug("build_netmap_layer2_graph() vlan mappings done")

    graph = nx.MultiDiGraph()
    # Make a copy of the graph, and add edge meta data
    for node_a, node_b, key in topology_without_metadata.edges_iter(keys=True):
        graph.add_edge(node_a, node_b, key=key,
            metadata=edge_metadata_layer2(key.netbox, key, node_b,
                key.to_interface, vlan_by_interface))

    _LOGGER.debug("build_netmap_layer2_graph() graph copy with metadata done")

    for node, data in graph.nodes_iter(data=True):
        if vlan_by_netbox.has_key(node):
            data['metadata'] = {
                'vlans': sorted(vlan_by_netbox.get(node).iteritems(),
                    key=lambda x: x[1].vlan.vlan)}
    _LOGGER.debug("build_netmap_layer2_graph() vlan metadata done")

    if view:
        graph = _attach_node_positions(graph, view.node_position_set.all())
    _LOGGER.debug("build_netmap_layer2_graph() view positions and graph done")
    return graph


def build_netmap_layer3_graph(view=None):
    """
    Builds a netmap layer 3 graph, based on nav's build_layer3_graph method.


    :param view A NetMapView for getting node positions according to saved
    netmap view.

    :return NetworkX MultiGraph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """
    _LOGGER.debug("build_netmap_layer3_graph() start")
    topology_without_metadata = vlan.build_layer3_graph(
        ('prefix__vlan__net_type', 'gwportprefix__prefix__vlan__net_type',))
    _LOGGER.debug("build_netmap_layer3_graph() topology graph done")

    vlans_map = _get_vlans_map_layer3(topology_without_metadata)
    _LOGGER.debug("build_netmap_layer2_graph() vlan mappings done")

    # Make a copy of the graph, and add edge meta data
    graph = nx.MultiGraph()

    for gwpp_a, gwpp_b, prefix in topology_without_metadata.edges_iter(
        keys=True):

        netbox_a = gwpp_a.interface.netbox
        netbox_b = gwpp_b.interface.netbox

        graph.add_edge(netbox_a, netbox_b, key=prefix.vlan.id,
            metadata=edge_metadata_layer3(gwpp_a, gwpp_b,
                vlans_map.get(prefix.vlan.id)))
    _LOGGER.debug("build_netmap_layer3_graph() graph copy with metadata done")

    if view:
        graph = _attach_node_positions(graph, view.node_position_set.all())
    _LOGGER.debug("build_netmap_layer3_graph() view positions and graph done")
    return graph


def _attach_node_positions(graph, node_set):
    """ Attaches node positions from a set of nodes which is extracted from a
    given map view earlier in the call stack.

    :param graph graph to modify metadata on
    :param node_set NetmapViewNodePosition collection for a given map view
    """

    # node is a tuple(netbox, networkx_graph_node_meta_dict)
    # Traversing our generated graph which misses node positions..
    for node in graph.nodes(data=True):
        # Find node metadata in saved map view if it has any.
        node_meta_dict = [x for x in node_set if x.netbox == node[0]]

        # Attached position meta data if map view has meta data on node in graph
        if node_meta_dict:
            if node[1].has_key('metadata'):
                # has vlan meta data, need to just update position data
                node[1]['metadata'].update({'position': node_meta_dict[0]})
            else:
                node[1]['metadata'] = {'position': node_meta_dict[0]}
    return graph



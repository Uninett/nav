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
import logging
import networkx as nx
import operator
from nav.models.manage import SwPortVlan, NetType
from nav.netmap import stubs
from nav.netmap.metadata import edge_metadata_layer3, edge_metadata
from nav.topology import vlan


_LOGGER = logging.getLogger(__name__)


def _get_vlans_map(graph):
    interface_id_list = list()
    for n, nbrdict, key in graph.edges_iter(keys=True):
        if key.vlan:
            interface_id_list.append(key.id)

    from collections import defaultdict
    vlan_by_interface = defaultdict(list)
    vlan_by_netbox = defaultdict(dict)
    for swpv in SwPortVlan.objects.filter(interface__in=list(interface_id_list)).select_related():
        vlan_by_interface[swpv.interface].append(swpv)

        # unique storing on internal nav vlan id
        vlan_by_netbox[swpv.interface.netbox].update({swpv.vlan.id:swpv})

    return (vlan_by_interface, vlan_by_netbox)

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
        ('to_interface__netbox', 'to_interface__netbox__room', 'to_netbox__room', 'netbox__room',))
    _LOGGER.debug("build_netmap_layer2_graph() topology graph done")

    vlan_by_interface, vlan_by_netbox = _get_vlans_map(topology_without_metadata)
    _LOGGER.debug("build_netmap_layer2_graph() vlan mappings done")

    graph = nx.MultiDiGraph()
    # Make a copy of the graph, and add edge meta data
    for n, nbrdict, key in topology_without_metadata.edges_iter(keys=True):
        graph.add_edge(n, nbrdict, key=key,
            metadata=edge_metadata(key.netbox, key, nbrdict, key.to_interface, vlan_by_interface))

    _LOGGER.debug("build_netmap_layer2_graph() graph copy with metadata done")

    for node, data in graph.nodes_iter(data=True):
        if vlan_by_netbox.has_key(node):
            data['metadata'] = {'vlans': sorted(vlan_by_netbox.get(node).iteritems(), key=lambda x: x[1].vlan.vlan)}

    if view:
        graph = _attach_node_positions(graph, view.node_position_set.all())
    _LOGGER.debug("build_netmap_layer2_graph() view positions and graph done")
    return graph


def build_netmap_layer3_graph(view=None):
    """
    Builds a netmap layer 3 graph, based on nav's build_layer3_graph method.


    :param view A NetMapView for getting node positions according to saved
    netmap view.

    :return NetworkX MultiDiGraph with attached metadata for edges and nodes
            (obs! metadata has direction metadata added!)
    """
    _LOGGER.debug("build_netmap_layer3_graph() start")
    topology_without_metadata = vlan.build_layer3_graph(('prefix__vlan__net_type',))
    #    ('to_interface__netbox__room', 'netbox__room', 'to_interface__to_netbox__room', 'interface__to_netbox__rom' 'to_interface__netbox', 'prefix__vlan__net_type',))
    _LOGGER.debug("build_netmap_layer3_graph() topology graph done")

    graph = nx.MultiDiGraph()
    # Make a copy of the graph, and add edge meta data
    for n, nbrdict, key in topology_without_metadata.edges_iter(keys=True):
        graph.add_edge(n, nbrdict, key=key,
            metadata=edge_metadata_layer3(key.interface.netbox, key, nbrdict,
                key.interface.to_interface))
    _LOGGER.debug("build_netmap_layer3_graph() graph copy with metadata done")

    # Find who has neighbors that NAV doesn't know anything about
    nodes_with_no_metadata = []

    elink_type = NetType.objects.get(id='elink')

    for node, nbr, key in graph.edges_iter(keys=True):
        if None in graph.neighbors(node) and not nbr and key.prefix.vlan.net_type==elink_type:
            nodes_with_no_metadata.append((node, nbr, key))

    # remove the global None node and it's related edges if it is there
    if graph.has_node(None):
        graph.remove_node(None)

    # elink fictive nodes named by ifalias / UNINETT convention
    for node, nbr, key in nodes_with_no_metadata:
        fictive_node = stubs.Netbox()
        if key.interface.ifalias:
            fictive_node.sysname = key.interface.ifalias
        else:
            fictive_node.sysname = '%s (%s) missing ifalias' % (key.interface.netbox,  key.interface)
        fictive_node.category_id = 'elink'
        graph.add_edge(node, fictive_node, key=key)
        graph.add_edge(fictive_node, node, key=key)

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



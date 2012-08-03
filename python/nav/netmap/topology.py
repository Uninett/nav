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
from nav.netmap.metadata import edge_metadata_layer3, edge_metadata
from nav.topology import vlan


_LOGGER = logging.getLogger(__name__)


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
        ('to_interface__netbox',))
    _LOGGER.debug("build_netmap_layer2_graph() topology graph done")
    graph = nx.MultiDiGraph()
    # Make a copy of the graph, and add edge meta data
    for n, nbrdict, key in topology_without_metadata.edges_iter(keys=True):
        graph.add_edge(n, nbrdict, key=key,
            metadata=edge_metadata(key.netbox, key, nbrdict, key.to_interface))
    _LOGGER.debug("build_netmap_layer2_graph() graph copy with metadata done")
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
    topology_without_metadata = vlan.build_layer3_graph(
        ('to_interface__netbox',))
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
    for node in graph.nodes_iter():
        neighbors = graph.neighbors(node)
        if None in neighbors:
            nodes_with_no_metadata.append(node)


    # remove the global None node and it's related edges if it is there
    if graph.has_node(None):
        graph.remove_node(None)

        # Time to add each node's UNKNOWN_EXIT_ROUTE
    i = 0
    for node in nodes_with_no_metadata:
        i += 1
        #fictive_node = Netbox()
        #fictive_node.sysname = node.sysname + ' EXTERNAL_EXIT_NODE'
        # Add fictive shadow box for each node EXIT, default gw route?,
        # undefined links?
        #graph.add_edge(node, root, key='internett%s'%i)

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
        if node_meta_dict and 'metadata' in node[1]:
            node[1]['metadata'] = node_meta_dict[0]
    return graph



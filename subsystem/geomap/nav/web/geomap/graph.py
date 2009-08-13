#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Graph representation and manipulation.



"""

import logging

from math import sqrt

from nav.web.geomap.coordinates import utm_str_to_lonlat
from nav.web.geomap.utils import *


logger = logging.getLogger('nav.web.geomap.graph')


# Specifications of how to combine the properties when combining nodes
# and edges:

aggregate_properties_place = {
    'load': (nansafe_max, 'load'),
    'num_rooms': len,
    'num_netboxes': (sum, 'num_netboxes'),
    'rooms': identity
    }

aggregate_properties_room = {
    'id': (first, 'roomid'),
    'descr': (first, 'room_descr'),
    'load': (nansafe_max, 'load'),
    'num_netboxes': len,
    'netboxes': identity
    }

aggregate_properties_edge = {
    'id': lambda edges: 'ce[%s]' % combine_ids(edges, lambda e: e['id']),
    'num_edges': len,
    'capacity': (sum, 'capacity'),
    'load_in': (sum, 'load_in'),
    'load_out': (sum, 'load_out'),
    'subedges': identity
    }


def build_graph(db_results):
    """Make a Graph object based on the dictionaries resulting from get_data.
    """
    (netboxes,connections) = db_results
    graph = Graph()

    # create Node objects:
    for netbox in netboxes:
        graph.add_node(Node(netbox['netboxid'], netbox['lon'], netbox['lat'],
                            netbox))

    # create Edge objects:
    for connection in connections.values():
        if (not connection['forward']['to_netboxid'] in graph.nodes or
            not connection['reverse']['to_netboxid'] in graph.nodes):
            continue
        graph.add_edge(Edge(connection['forward']['id'],
                            graph.nodes[connection['forward']['from_netboxid']],
                            graph.nodes[connection['forward']['to_netboxid']],
                            connection['reverse'],
                            connection['forward']))

    return graph


def simplify(graph, bounds, viewport_size, limit):
    """Remove and combine edges and nodes in a graph.

    Objects outside the interesting area (given by bounds) are
    removed, and those that are inside are combined so that they are
    not too close together (based on viewport_size and limit).

    Arguments:

    graph -- the Graph object to simplify.  It is destructively
    modified.

    bounds -- a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    viewport_size -- a dictionary with keys (width, height), the width
    and height of the user's viewport for the map in pixels.

    limit -- the minimum distance (in pixels) there may be between two
    points without them being collapsed to one.

    """
    area_filter(graph, bounds)
    create_rooms(graph)
    create_places(graph, bounds, viewport_size, limit)
    combine_edges(graph, aggregate_properties_edge)


def area_filter(graph, bounds):
    """Restrict a graph to a geographical area.

    Removes objects outside bounds from graph.  An edge is retained if
    at least one of its endpoints is inside bounds.  A node is
    retained if it is an endpoint of such an edge (even if the node
    itself is outside bounds).

    Arguments:

    graph -- the Graph object to filter.  It is destructively
    modified.

    bounds -- a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    """
    def in_bounds(n):
        return \
            n.lon>=bounds['minLon'] and n.lon<=bounds['maxLon'] and \
            n.lat>=bounds['minLat'] and n.lat<=bounds['maxLat']
    def edge_connected_to(edge, nodehash):
        return edge.source.id in nodehash or edge.target.id in nodehash
    nodes = filter_dict(in_bounds, graph.nodes)
    edges = filter_dict(lambda edge: edge_connected_to(edge, nodes),
                        graph.edges)
    node_ids = (set(nodes.keys())
                | set([e.source.id for e in edges.values()])
                | set([e.target.id for e in edges.values()]))
    graph.nodes = subdict(graph.nodes, node_ids)
    graph.edges = edges


def create_rooms(graph):
    """Convert a graph of netboxes to a graph of rooms.

    graph is assumed to have one nodes representing netboxes.  These
    are combined so that there is one node for each room.  Each room
    node has a property 'netboxes' (available as
    roomnode.properties['netboxes']) which is a list of the original
    nodes it is based on.

    Arguments:

    graph -- a Graph object.  It is destructively modified.
    
    """
    collapse_nodes(graph,
                   group(lambda node: node.properties['roomid'],
                         graph.nodes.values()),
                   'netboxes',
                   aggregate_properties_room)


def create_places(graph, bounds, viewport_size, limit):
    """Convert a graph of rooms to a graph of 'places'.

    A 'place' is a set of one or more rooms.  The position of a place
    is the average of the positions of its rooms.  The places are
    created such that no two places are closer than limit to each
    other.  Each place node has a property 'rooms' (available as
    placenode.properties['rooms']) which is a list of the room nodes
    it is based on.

    Arguments:

    graph -- a Graph object.  It is destructively modified.
    
    bounds -- a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    viewport_size -- a dictionary with keys (width, height), the width
    and height of the user's viewport for the map in pixels.

    limit -- the minimum distance (in pixels) there may be between two
    points without them being collapsed to one.

    """
    # TODO:
    #
    # -- This may give division by zero with bogus input (should check
    #    for zeros -- what should we do then?)
    #
    # -- Should take into account that longitudes wrap around. Is
    #    there any way to detect whether we have a map wider than the
    #    earth, or do we need an extra parameter?
    width = bounds['maxLon']-bounds['minLon']
    height = bounds['maxLat']-bounds['minLat']
    lon_scale = float(viewport_size['width'])/width
    lat_scale = float(viewport_size['height'])/height
    def square(x): return x*x
    def distance(n1, n2):
        return sqrt(square((n1.lon-n2.lon)*lon_scale) +
                    square((n1.lat-n2.lat)*lat_scale))
    places = []
    for node in graph.nodes.values():
        for place in places:
            if distance(node, place['position']) < limit:
                place['rooms'].append(node)
                place['position'].lon = avg([n.lon for n in place['rooms']])
                place['position'].lat = avg([n.lat for n in place['rooms']])
                break
        else:
            places.append({'position': Node(None, node.lon, node.lat, None),
                           'rooms': [node]})
    collapse_nodes(graph,
                   [place['rooms'] for place in places],
                   'rooms',
                   aggregate_properties_place)


def collapse_nodes(graph, node_sets, subnode_list_name,
                   property_aggregators={}):
    """Collapse sets of nodes to single nodes.

    Replaces each set of nodes in node_sets by a single (new) node and
    redirects the edges correspondingly.  Edges which would end up
    having both endpoints in the same node are removed.

    Each new node is positioned at the average of the positions of the
    node set it represents.  It also gets a property containing the
    original nodes; the name of this property is given by
    subnode_list_name.

    Properties from the original nodes may be combined to form
    aggregate values in the new node.  The property_aggregators
    argument determines how (and whether) this is done.  Some useful
    aggregator functions are sum and avg (for numbers) and lambda lst:
    ', '.join(map(str, lst)).

    Arguments:

    graph -- a Graph object.  It is destructively modified.

    node_sets -- a list of lists of nodes in graph.  Each node should
    occur in exactly one of the lists.

    subnode_list_name -- name for the property containing the original
    nodes a newly created node represents.

    property_aggregators -- describes how to create aggregate
    properties.  Dictionary with names of properties as keys and
    aggregator functions as corresponding values.  Each aggregator
    function should take a single argument, a list.

    """
    graph.nodes = {}
    nodehash = {}
    for s in node_sets:
        properties = aggregate_properties(map(lambda node: node.properties, s),
                                          property_aggregators)
        new_node = Node('cn[%s]' % combine_ids(s),
                        avg([n.lon for n in s]), avg([n.lat for n in s]),
                        properties)
        for n in s:
            nodehash[n.id] = new_node
        graph.add_node(new_node)
    # Now nodehash maps original node ids to new node objects.  Use it
    # to redirect the edges to the new nodes:
    for edge in graph.edges.values():
        edge.source = nodehash[edge.source.id]
        edge.target = nodehash[edge.target.id]
    graph.edges = filter_dict(lambda edge: edge.source != edge.target,
                              graph.edges)


def combine_ids(objects, get_id=lambda o: o.id):
    """Combine the IDs of a list (or set) of objects to a string.

    Used when generating IDs for collapsed objects.  The IDs are
    sorted so that the resulting ID is uniquely determined by the set
    of objects.

    """
    ids = [str(get_id(o)) for o in objects]
    ids.sort()
    return ';'.join(ids)


def aggregate_properties(objects, aggregators):
    """Combine the properties of a list of objects.

    Constructs a lazy dictionary (see class lazy_dict in utils.js) of
    properties.

    Arguments:

    objects -- a list of Node or Edge objects

    aggregators -- dictionary, specifies how to combine the
    properties. For each item in aggregators, a property with the same
    key is created. The aggregator value should be either a function,
    in which case the property value is created by calling that
    function on the list of objects; or a pair (function, prop), in
    which case the property value is created by calling the function
    on a list containing each object's value for property prop.

    """
    def apply_aggregator(aggr):
        if isinstance(aggr, tuple):
            fun = aggr[0]
            property = aggr[1]
            lst = map(lambda o: o[property], objects)
        else:
            fun = aggr
            lst = objects
        return fun(lst)
    return map_dict_lazy(apply_aggregator, aggregators)

#     return dict(map(lambda (property, aggregator):
#                         (property,
#                          aggregator(map(lambda obj: obj.properties[property],
#                                         objects))),
#                     aggregators.items()))
    

def combine_edges(graph, property_aggregators={}):
    """Combine edges with the same endpoints.

    Replaces the edges in graph with new edge objects, where any set
    of edges between the same two nodes is replaced by a single edge.
    Each new edge has a property 'subedges'
    (edge.properties['subedges']) which contains the original edge
    objects.

    Arguments:

    graph -- a Graph object.  It is destructively modified.

    """
    edges_by_node = dict([(id, set()) for id in graph.nodes])
    for edge in graph.edges.values():
        edges_by_node[edge.source.id].add(edge)
        edges_by_node[edge.target.id].add(edge)
    edge_sets = {}
    for edge in graph.edges.values():
        if edge.id in edge_sets:
            continue
        eset = list(edges_by_node[edge.source.id] &
                    edges_by_node[edge.target.id])
        for e in eset:
            edge_sets[e] = eset

    edge_sets = map_dict(equalize_edge_orientation, edge_sets)

    edges = map(
        lambda eset:
            Edge('ce[%s]' % combine_ids(eset),
                 eset[0].source,
                 eset[0].target,
                 aggregate_properties(map(lambda edge: edge.sourceData, eset),
                                      property_aggregators),
                 aggregate_properties(map(lambda edge: edge.targetData, eset),
                                      property_aggregators)),
        edge_sets.values())
    graph.edges = dict([(e.id,e) for e in edges])


def equalize_edge_orientation(edges):
    """Make all edges have the same direction.

    Arguments:

    edges -- list of edges between the same pair of nodes

    """
    reference = edges[0]
    def fix_orientation(edge):
        if edge.source != reference.source:
            return reverse_edge(edge)
        return edge
    return map(fix_orientation, edges)


def reverse_edge(edge):
    """Reverse the direction of an edge.

    Returns a new Edge object; the argument is not modified.

    """
    return Edge(edge.sourceData['id'],
                edge.target, edge.source,
                edge.targetData, edge.sourceData)


class Node:
    """Representation of a node in a graph."""
    def __init__(self, id, lon, lat, properties):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.properties = properties


class Edge:
    """Representation of an edge in a graph."""
    def __init__(self, id, source, target, sourceData, targetData):
        self.id = id
        self.source = source
        self.target = target
        self.sourceData = sourceData
        self.targetData = targetData


class Graph:
    """Representation of a graph of geographical positions."""
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, n):
        self.nodes[n.id] = n

    def add_edge(self, e):
        self.edges[e.id] = e





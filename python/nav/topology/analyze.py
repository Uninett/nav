#
# Copyright (C) 2011,2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Reduction of network adjacency candidates graph.

This module uses NetworkX to facilitate reduction of NAV's network adjacency
candidates graph (loaded from the adjacency_candidate table) into a proper
physical topology graph.

The adjacency_candidate_netbox table can be loaded as a directed graph, from
which reduction can take place.

The graph can be analyzed and reduced by using the AdjacencyReducer class.


Graph structure
===============

A proper adjacency graph must consist only of Box and Port objects, as defined
in this module.

Netbox nodes must only have outgoing edges to Port nodes representing the
Netbox' own interfaces.

Port nodes can have outgoing edges to other Port nodes, or to Netbox nodes

"""
# pylint: disable=R0903

from itertools import groupby
from operator import attrgetter

import networkx as nx
from nav.models.manage import AdjacencyCandidate

# Data classes

class Box(int):
    """A Netbox' netboxid value"""
    name = None

    def __str__(self):
        return self.name or super(Box, self).__str__()

class Port(tuple):
    """An Interface's (netboxid, interfaceid) values"""
    name = None

    def __str__(self):
        return self.name or super(Port, self).__str__()


# Analyzers

class AdjacencyAnalyzer(object):
    """Adjacency candidate graph analyzer and manipulator"""

    def __init__(self, graph):
        self.graph = graph

    def get_max_out_degree(self):
        """Returns the port node with the highest outgoing degree"""
        ports_and_degree = self.get_ports_and_degree()
        maximum = max(ports_and_degree) if ports_and_degree else None
        if maximum:
            return maximum[0]
        else:
            return 0

    def get_ports_ordered_by_degree(self):
        """Return a list of port nodes from the Graph, ordered by degree."""
        ports_and_degree = self.get_ports_and_degree()
        ports_and_degree.sort()
        return [port for _degree, port in ports_and_degree]


    def find_return_path(self, edge):
        """Find a return path starting along edge from a port node.

        In the typical network adjacency candidates graph, a return path will
        consist of no more than 5 nodes, including the source node at both
        ends of the path.

        """
        from_port, to_thing = edge
        from_netbox = from_port[0]

        # Initial known element of the path
        path = [from_port]

        if type(to_thing) is Box:
            # Remote was a netbox, so we need to check each of the netbox'
            # outgoing ports to find a path
            remote_ports = [e[1] for e in self.graph.edges(to_thing)]
        else:
            remote_ports = [to_thing]

        for remote_port in remote_ports:
            for remote_edge in self.graph.edges(remote_port):
                remote_thing = remote_edge[1]
                if type(remote_thing) is Box and remote_thing == from_netbox:
                    path.extend([remote_port, remote_thing, from_port])
                    return path
                elif remote_thing == from_port:
                    path.extend([remote_port, remote_thing])
                    return path

        return []

    @staticmethod
    def get_distinct_ports(path):
        """Return a distinct list of ports listed in path"""
        result = []
        for node in path:
            if type(node) is Port and node not in result:
                result.append(node)
        return result

    def connect_ports(self, i, j):
        """Remove existing arcs from a and b and connect them.

        a's outgoing edges are replaced by a single outgoing edge to b.
        b's outgoing edges are replaced by a single outgoing edge to a.

        Oncee two ports are connected, incoming edges from other ports are no
        longer relevant and are deleted.

        """
        self._delete_edges(i)
        self._delete_edges(j)

        self.delete_incoming_edges_from_ports(i)
        self.delete_incoming_edges_from_ports(j)

        self.graph.add_edge(i, j)
        self.graph.add_edge(j, i)

    def _delete_edges(self, node):
        """Deletes all outgoing edges from node"""
        # this stupidity is here to support the changing NetworkX APIs
        if hasattr(self.graph, 'delete_edges_from'):
            self.graph.delete_edges_from(self.graph.edges(node))
        else:
            self.graph[node].clear()

    def delete_incoming_edges_from_ports(self, node):
        """Deletes all edges coming in from ports to node"""
        edges_from_ports = [(u, v) for u, v in self.graph.in_edges(node)
                            if type(u) is Port]
        if hasattr(self.graph, 'delete_edges_from'):
            self.graph.delete_edges_from(edges_from_ports)
        else:
            self.graph.remove_edges_from(edges_from_ports)

    def get_ports_and_degree(self):
        """Return a list of port nodes and their outgoing degrees.

        Result:

          A list of tuples: [(degree, node), ... ]

        """
        result = [(self.graph.out_degree(n), n)
                  for n in self.graph.nodes()
                  if type(n) is Port]
        return result

    def format_connections(self):
        """Returns a formatted string representation of all outgoing edges
        from ports.

        """
        output = ["%s => %s" % (source, dest)
                  for source, dest in self.get_single_edges_from_ports()]
        output.sort()
        return "\n".join(output)

    def get_single_edges_from_ports(self):
        """Returns a list of edges from ports whose degree is 1"""
        edges = [self.graph.edges(port)[0]
                 for port in self.get_ports_by_degree(1)]
        return edges

    def get_ports_by_degree(self, degree):
        """Returns a list of port nodes with a given out_degree"""
        port_nodes = [n for n in self.graph.nodes()
                      if type(n) is Port and self.graph.out_degree(n) == degree]
        return port_nodes

    def port_in_degree(self, port):
        """Returns the in_degree of the port node, only counting outgoing
        edges from ports, not boxes.

        """
        return len([(u, v) for (u, v) in self.graph.in_edges(port)
                    if type(u) is Port])

    def get_incomplete_ports(self):
        """Return a list of port nodes whose outgoing edges have not been
        successfully reduced to one.

        """
        ports_and_degree = self.get_ports_and_degree()
        return [port for degree, port in ports_and_degree
                if degree > 1]

    def get_boxes_without_ports(self):
        """Return a list of netboxes that have no outgoing edges."""
        result = [n for n in self.graph.nodes()
                  if type(n) is Box and
                  self.graph.out_degree(n) == 0]
        return result

class AdjacencyReducer(AdjacencyAnalyzer):
    """Adjacency candidate graph reducer"""

    def reduce(self):
        """Reduces the associated graph.

        This will reduce the graph as much as possible.  After the graph has
        been reduced, any port (tuple) node with an out_degree of 1 should be
        ready to store as part of the physical topology.

        """
        max_degree = self.get_max_out_degree()
        degree = 1

        visited = set()
        while degree <= max_degree:
            unvisited = self._get_unvisited_by_degree(degree, visited)
            if len(unvisited) == 0:
                degree += 1
                continue

            self._visit_unvisited(unvisited, visited)

    def _get_unvisited_by_degree(self, degree, visited):
        ports = set(self.get_ports_by_degree(degree))
        return ports.difference(visited)

    def _visit_unvisited(self, unvisited, visited):
        for port in unvisited:
            for source, dest in self.graph.edges(port):

                if (self.graph.out_degree(source) == 1 and
                    type(dest) is Port):
                    self.connect_ports(source, dest)
                    visited.add(dest)

                else:

                    path = self.find_return_path((source, dest))
                    if path:
                        i, j = self.get_distinct_ports(path)
                        self.connect_ports(i, j)
                        visited.update((i, j))
                        break

            visited.add(port)

# Graph builder functions

def build_candidate_graph_from_db():
    """Builds and returns a DiGraph conforming to the requirements of an
    AdjacencyAnalyzer, based on data found in the adjacency_candidate database
    table.

    """
    acs = AdjacencyCandidate.objects.select_related(
        'netbox', 'interface', 'to_netbox', 'to_interface')
    acs = _filter_by_source(acs)

    graph = nx.DiGraph(name="network adjacency candidates")

    for cand in acs:
        if cand.to_interface:
            dest_node = Port((cand.to_netbox.id,
                              cand.to_interface.id))
            dest_node.name = "%s (%s)" % (cand.to_netbox.sysname,
                                          cand.to_interface.ifname)
        else:
            dest_node = Box(cand.to_netbox.id)
            dest_node.name = cand.to_netbox.sysname

        port = Port((cand.netbox.id, cand.interface.id))
        port.name = "%s (%s)" % (cand.netbox.sysname, cand.interface.ifname)
        netbox = Box(cand.netbox.id)
        netbox.name = cand.netbox.sysname

        graph.add_edge(port, dest_node)
        graph.add_edge(netbox, port)


    return graph

CDP = 'cdp'
LLDP = 'lldp'

def _filter_by_source(all_candidates):
    """Filters candidates from list based on their source.

    For each interface, LLDP is preferred over CDP, CDP is preferred over
    anything else.

    """
    key = attrgetter('interface.id')
    all_candidates = sorted(all_candidates, key=key)
    by_ifc = groupby(all_candidates, key)

    for _ifc, candidates in by_ifc:
        candidates = list(candidates)
        sources = set(c.source for c in candidates)
        if LLDP in sources:
            candidates = (c for c in candidates if c.source == LLDP)
        elif CDP in sources:
            candidates = (c for c in candidates if c.source == CDP)

        for candidate in candidates:
            yield candidate

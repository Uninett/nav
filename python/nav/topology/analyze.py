#
# Copyright (C) 2011, 2012, 2015, 2017, 2018 UNINETT AS
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

import networkx as nx
from nav.models.manage import AdjacencyCandidate

import logging
_logger = logging.getLogger(__name__)

CDP = 'cdp'
LLDP = 'lldp'

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

    def find_return_port(self, from_port, to_netbox):
        """Given a candidate edge from from_port to to_netbox, find a port at
        to_netbox that points to from_port's netbox
        """
        from_netbox = from_port[0]

        # Remote is a netbox, we need to check each of the netbox'
        # outgoing ports to find a path
        remote_ports = self.graph.neighbors(to_netbox)

        for remote_port in remote_ports:
            for remote_edge in self.graph.edges(remote_port):
                remote_netbox = remote_edge[1]
                if remote_netbox == from_netbox:
                    return remote_port

        return None

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


class AdjacencyReducer(AdjacencyAnalyzer):
    """Adjacency candidate graph reducer"""

    def reduce(self):
        """Find physical topology based on the graph

        First LLDP and CDP data is analyzed. Then CAM data. The result
        is stored in a new graph which can then be used to update
        physical topology

        """
        self.result = nx.DiGraph(name="network adjacency candidates")
        self._reduce_discovery_protocol(LLDP)
        self._reduce_discovery_protocol(CDP)
        self._reduce_cam()
        self.graph = self.result

    def _reduce_cam(self):
        """Find topology based on CAM data.

        The algorithm iterates over graph nodes starting with the
        lowest order nodes. Then the outward edges of the node is
        iterated over and if an edge is found where a suitable return
        path is found the pair of nodes are removed from the graph and
        added to the result, thus reducing the order of the remaining
        nodes so that connections for these can be deduced more
        correctly.

        After the graph has been reduced, any port (tuple) node with
        an out_degree of 1 are added to the result
        """
        max_degree = self.get_max_out_degree()
        _logger.debug("Analyzing graph with max degree %d", max_degree)
        degree = 1

        while degree <= max_degree:
            _logger.debug("At degree %s", degree)
            unvisited = self.get_ports_by_degree(degree)
            _logger.debug("Found %d unvisited ports", len(unvisited))
            if len(unvisited) == 0:
                degree += 1
                continue

            if not self._visit_unvisited(unvisited):
                degree += 1
                continue
        self.result.add_edges_from(self.get_single_edges_from_ports())

    def _reduce_discovery_protocol(self, sourcetype):
        done = False
        while not done:
            done = True
            for source, dest, proto in self.graph.edges(keys=True):
                if (not type(source) is Port or not type(dest) is Port or
                        proto != sourcetype):
                    continue
                if source == dest:
                    _logger.info("Ignoring apparent %s self-loop on %s",
                                 proto, source)
                    self.graph.remove_edge(source, dest, proto)
                    continue
                if self.graph.has_edge(dest, source, proto):
                    _logger.debug("Found connection from %s to %s", source,
                                  dest)
                    self.result.add_edge(source, dest)
                    self.result.add_edge(dest, source)
                    self.graph.remove_node(source)
                    self.graph.remove_node(dest)
                    done = False
                    break
                else:
                    _logger.debug("Removing unmatched %s connection %s -> %s",
                                  proto, source, dest)
                    self.graph.remove_edge(source, dest, proto)

    def _visit_unvisited(self, unvisited):
        for port in unvisited:
            for source, dest, proto in self.graph.edges(port, keys=True):
                _logger.debug("Considering %s %s source %s",
                              source, dest, proto)
                if dest == source[0]:
                    _logger.warning("A possible self-loop was found: "
                                    "%r", (source, dest))
                    self.graph.remove_edge(source, dest)
                    continue

                remote_port = self.find_return_port(source, dest)
                if remote_port:
                    _logger.debug("Found connection %s -> %s because of good return path",
                                  source, remote_port)
                    self.connect_ports(source, remote_port)
                    return True
            _logger.debug("Found no connection for %s", port)
        return False

    def connect_ports(self, i, j):
        """Add connection between a and b to result.

        If a or b are of type Port they are removed from the input
        graph, as they are now completely processed

        """
        if type(i) is Port:
            self.graph.remove_node(i)
        if type(j) is Port:
            self.graph.remove_node(j)

        self.result.add_edge(i, j)
        self.result.add_edge(j, i)

# Graph builder functions


def build_candidate_graph_from_db():
    """Builds and returns a DiGraph conforming to the requirements of an
    AdjacencyAnalyzer, based on data found in the adjacency_candidate database
    table.

    """
    acs = AdjacencyCandidate.objects.select_related(
        'netbox', 'interface', 'to_netbox', 'to_interface')

    graph = nx.MultiDiGraph(name="network adjacency candidates")

    for cand in acs:
        if not cand.interface.is_admin_up():
            continue  # ignore data from disabled interfaces
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

        graph.add_edge(port, dest_node, cand.source)
        graph.add_edge(netbox, port)

    return graph

# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Uninett AS
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
"""Functions for topological sorting of graph nodes."""


def build_graph(objects, dependency_calculator):
    """Return a graph representation of the objects list.

    Arguments:

        objects -- a list of objects (nodes) in the graph
        dependency_calculator -- a function that takes an object as its
                                 argument and returns a list of its dependent
                                 objects.

    Returns:

       A dictionary describing the edges/arcs between the nodes in the graph:

       {'A': ['B', 'C'],  # Directed edges from 'A' to 'B' and 'C'
        'B': ['D'],       # Directed edges from 'B' to 'D'
        'C': [],          # No directed edges from C
        'D': []           # No directed edges from D
       }

    """
    graph = {}
    for obj in objects:
        dependencies = dependency_calculator(obj)
        graph[obj] = dependencies
        # safeguard to make sure all nodes are represented as keys
        for other_obj in dependencies:
            if other_obj not in graph:
                graph[other_obj] = []
    return graph


def topological_sort(graph):
    """Sort a graph of nodes topologically.

    Uses the algorithm described by Cormen, Leiserson & Rivest (1990).

    Arguments:

      nodes -- A dictionary describing a graph of node objects, such as the
               ones returned from the build_graph() function.


    Returns:

      A new list with the sorted nodes.

    """
    sorted_nodes = []
    all_nodes = graph.keys()
    visited = set()

    def visit(node):
        if node not in visited:
            visited.add(node)
            for other_node in graph[node]:
                visit(other_node)
            sorted_nodes.append(node)

    for node in all_nodes:
        visit(node)

    return sorted_nodes

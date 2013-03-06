#!/usr/bin/env python
# encoding: utf-8
#pylint: disable-all
"""
d3_js.py

Description: Read and write files in the D3.js JSON file format.  This
can be used to generate interactive Java Script embeds from NetworkX
graph objects.

These functions will read and write the D3.js JavaScript Object Notation (JSON)
format for a graph object. There is also a function to write write HTML and
Javascript
files need to render force-directed layout of graph object in a browser.  The
 default
redering options are based on the force-directed example by Mike Bostock at
(http://mbostock.github.com/d3/ex/force.html).

Created by Drew Conway (drew.conway@nyu.edu) on 2011-07-13 
# Copyright (c) 2011, under the Simplified BSD License.  
# For more information on FreeBSD see: http://www.opensource
.org/licenses/bsd-license.php
# All rights reserved.
"""

__author__ = """Drew Conway (drew.conway@nyu.edu)"""

import networkx as nx
from nav.netmap.metadata import node_to_json_layer2, node_to_json_layer3, edge_to_json_layer2, edge_to_json_layer3
from nav.netmap.rrd import attach_rrd_data_to_edges
import logging

"""
comment norangshol:
 is_string_like and make_str taken from https://github.com/drewconway/networkx
 networkx.utils , available under BSD license.

 modified to include metadata for nodes if metadata is specified in graph
 and removed file export.
"""

_LOGGER = logging.getLogger(__name__)


def is_string_like(obj): # from John Hunter, types-free version
    """Check if obj is string."""
    try:
        obj + ''
    except (TypeError, ValueError):
        return False
    return True


def make_str(t):
    """Return the string representation of t."""
    if is_string_like(t): return t
    return str(t)


def d3_json_layer2(G, group=None):
    return d3_json(G, node_to_json_layer2, edge_to_json_layer2, group)

def d3_json_layer3(G, group=None):
    return d3_json(G, node_to_json_layer3, edge_to_json_layer3, group)

def d3_json(G, node_to_json_function, edge_to_json_function, group=None):
    """Converts a NetworkX Graph to a properly D3.js JSON formatted dictionary

     Parameters
     ----------
     G : graph
         a NetworkX graph
     group : string, optional
         The name 'group' key for each node in the graph. This is used to
         assign nodes to exclusive partitions, and for node coloring if
         visualizing.

     Examples
     --------
     >>> from networkx.readwrite import d3_js
     >>> G = nx.path_graph(4)
     >>> G.add_nodes_from(map(lambda i: (i, {'group': i}), G.nodes()))
     >>> d3_js.d3_json(G)
     {'links': [{'source': 0, 'target': 1, 'value': 1},
       {'source': 1, 'target': 2, 'value': 1},
       {'source': 2, 'target': 3, 'value': 1}],
      'nodes': [{'group': 0, 'nodeName': 0},
       {'group': 1, 'nodeName': 1},
       {'group': 2, 'nodeName': 2},
       {'group': 3, 'nodeName': 3}]}
     """
    _LOGGER.debug("netmap:d3_json() start")
    ints_graph = nx.convert_node_labels_to_integers(G, discard_old_labels=False)
    graph_nodes = ints_graph.nodes(data=True)
    graph_edges = ints_graph.edges(data=True)

    node_labels = [(b, a) for (a, b) in ints_graph.node_labels.items()]
    node_labels.sort()
    _LOGGER.debug("netmap:d3_json() basic done")
    # Build up node dictionary in JSON format
    if group is None:
        graph_json = {'nodes': map(
            lambda n: {'name': unicode(node_labels[n][1].sysname), 'group': 0,
                       'data': node_to_json_function(node_labels[n][1],
                           graph_nodes[n][1])},
            xrange(len(node_labels)))}
    else:
        try:
            graph_json = {'nodes': map(
                lambda n: {'name': unicode(node_labels[n][1].sysname),
                           'group': graph_nodes[n][1][group],
                           'data': node_to_json_function(node_labels[n][1],
                               graph_nodes[n][1]['metadata'] if 'metadata' in
                                                                graph_nodes[n][
                                                                1] else None)},
                xrange(len(node_labels)))}
        except KeyError:
            raise nx.NetworkXError(
                "The graph had no node attribute for '" + group + "'")
    _LOGGER.debug("netmap:d3_json() nodes done")
    # Build up edge dictionary in JSON format

    json_edges = list()
    for j, k, w in ints_graph.edges_iter(data=True):
        e = {'source': node_labels[j][1].sysname, 'target': node_labels[k][1].sysname,
             'data': edge_to_json_function(w['metadata']) if 'metadata' in w else { 'traffic': {}}}
        if any(map(lambda k: k == 'weight', w.keys())):
            e['value'] = w['weight']
        else:
            e['value'] = 1
        json_edges.append(e)
    _LOGGER.debug("netmap:d3_json() edges done")
    json_edges = attach_rrd_data_to_edges(ints_graph, json_edges)
    _LOGGER.debug("netmap:d3_json() edges_fake_rrd done")
    graph_json['links'] = json_edges

    return graph_json




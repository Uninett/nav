#
# Copyright (C) 2008, 2009, 2011 UNINETT AS
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

import unittest
import networkx as nx
from mock import Mock
from nav.models.manage import Netbox, Interface
from netmapgraph_testcase import NetmapGraphTestCase


class MultiDiGraphToGraphTests(NetmapGraphTestCase):


    def test_multidigraph_to_graph(self):
        self.assertEquals(len(self.graph.edges(data=True)), 2)
        g = self.graph

        g = nx.Graph(g)
        #g = nx.Graph(g.edges(data=True)) # this will make test fail fyi!
        #g = nx.Graph(g.to_undirected()) # this will make test fail fyi!

        self.assertEquals(len(g.edges(data=True)), 1)

        ints_graph = nx.convert_node_labels_to_integers(g, discard_old_labels=False)
        graph_nodes = ints_graph.nodes(data=True)
        graph_edges = ints_graph.edges(data=True)

        node_labels = [(b, a) for (a, b) in ints_graph.node_labels.items()]
        node_labels.sort()

        self.assertEquals(len(graph_edges), 1)
        self.assertEquals(len(graph_nodes), 2)

        for from_index,to_index,metadata in graph_edges:
            metadata = metadata['metadata']
            self.assertEquals(node_labels[from_index][1], metadata['thiss'][0])
            self.assertEquals(node_labels[to_index][1], metadata['other'][0])

if __name__ == '__main__':
    unittest.main()
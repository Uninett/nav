# Copyright (C) 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import networkx as nx

from nav.topology.analyze import AdjacencyReducer, Box, Port


class TestAdjecencyReducer(object):
    """Tests for nav.topology.analyze.AdjecencyReducer class"""

    @classmethod
    def setup_class(cls):
        cls.router_id = 1
        cls.switch_a_id = 2
        cls.switch_b_id = 3
        cls.router = Box(cls.router_id)
        cls.router.name = "router"
        cls.switch_a = Box(cls.switch_a_id)
        cls.switch_a.name = "switch a"
        cls.switch_b = Box(cls.switch_b_id)
        cls.switch_b.name = "switch b"
        cls.router_port_a = Port((cls.router_id, cls.switch_a_id))
        cls.router_port_a.name = "router port a"
        cls.router_port_b = Port((cls.router_id, cls.switch_b_id))
        cls.router_port_b.name = "router port b"
        cls.switch_port_a = Port((cls.switch_a_id, 1))
        cls.switch_port_a.name = "switch port a"
        cls.switch_port_b = Port((cls.switch_b_id, 1))
        cls.switch_port_b.name = "switch port b"

    def test_reduce_simple_case_cam(self):
        graph = nx.MultiDiGraph(name="simple case cam")
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.switch_b, "cam")
        graph.add_edge(self.switch_port_b, self.switch_a, "cam")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert result.has_edge(self.switch_port_a, self.switch_port_b)
        assert result.has_edge(self.switch_port_b, self.switch_port_a)
        assert result.out_degree(self.switch_port_a) == 1
        assert result.out_degree(self.switch_port_b) == 1

    def test_reduce_simple_case_lldp(self):
        graph = nx.MultiDiGraph(name="simple case lldp")
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.switch_port_b, "lldp")
        graph.add_edge(self.switch_port_b, self.switch_port_a, "lldp")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert result.has_edge(self.switch_port_a, self.switch_port_b)
        assert result.has_edge(self.switch_port_b, self.switch_port_a)
        assert result.out_degree(self.switch_port_a) == 1
        assert result.out_degree(self.switch_port_b) == 1

    def test_reduce_simple_tree_lldp(self):
        graph = nx.MultiDiGraph(name="simple tree lldp")
        graph.add_edge(self.router, self.router_port_a)
        graph.add_edge(self.router, self.router_port_b)
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.router_port_a, "lldp")
        graph.add_edge(self.switch_port_b, self.router_port_b, "lldp")
        graph.add_edge(self.router_port_a, self.switch_port_a, "lldp")
        graph.add_edge(self.router_port_b, self.switch_port_b, "lldp")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert result.has_edge(self.switch_port_a, self.router_port_a)
        assert result.has_edge(self.switch_port_b, self.router_port_b)
        assert result.has_edge(self.router_port_a, self.switch_port_a)
        assert result.has_edge(self.router_port_b, self.switch_port_b)
        assert result.out_degree(self.switch_port_a) == 1
        assert result.out_degree(self.switch_port_b) == 1
        assert result.out_degree(self.router_port_a) == 1
        assert result.out_degree(self.router_port_b) == 1

    def test_reduce_simple_tree_cam(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(self.router, self.router_port_a)
        graph.add_edge(self.router, self.router_port_b)
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)

        graph.add_edge(self.switch_port_a, self.router, "cam")
        graph.add_edge(self.switch_port_b, self.router, "cam")
        graph.add_edge(self.router_port_a, self.switch_a, "cam")
        graph.add_edge(self.router_port_b, self.switch_b, "cam")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert result.has_edge(self.switch_port_a, self.router_port_a)
        assert result.has_edge(self.switch_port_b, self.router_port_b)
        assert result.has_edge(self.router_port_a, self.switch_port_a)
        assert result.has_edge(self.router_port_b, self.switch_port_b)
        assert result.out_degree(self.switch_port_a) == 1
        assert result.out_degree(self.switch_port_b) == 1
        assert result.out_degree(self.router_port_a) == 1
        assert result.out_degree(self.router_port_b) == 1

    def test_reduce_tree_cam(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(self.router, self.router_port_a)
        graph.add_edge(self.router, self.router_port_b)
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)

        graph.add_edge(self.switch_port_a, self.router, "cam")
        graph.add_edge(self.switch_port_a, self.switch_b, "cam")
        graph.add_edge(self.switch_port_b, self.router, "cam")
        graph.add_edge(self.switch_port_b, self.switch_a, "cam")
        graph.add_edge(self.router_port_a, self.switch_a, "cam")
        graph.add_edge(self.router_port_b, self.switch_b, "cam")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert result.has_edge(self.switch_port_a, self.router_port_a)
        assert result.has_edge(self.switch_port_b, self.router_port_b)
        assert result.has_edge(self.router_port_a, self.switch_port_a)
        assert result.has_edge(self.router_port_b, self.switch_port_b)
        assert result.out_degree(self.switch_port_a) == 1
        assert result.out_degree(self.switch_port_b) == 1
        assert result.out_degree(self.router_port_a) == 1
        assert result.out_degree(self.router_port_b) == 1

    def test_reduce_simple_lldp_tree_and_cam(self):
        graph = nx.MultiDiGraph(name="simple tree lldp")
        graph.add_edge(self.router, self.router_port_a)
        graph.add_edge(self.router, self.router_port_b)
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.router_port_a, "lldp")
        graph.add_edge(self.switch_port_b, self.router_port_b, "lldp")
        graph.add_edge(self.router_port_a, self.switch_port_a, "lldp")
        graph.add_edge(self.router_port_b, self.switch_port_b, "lldp")
        graph.add_edge(self.switch_port_a, self.router, "cam")
        graph.add_edge(self.switch_port_a, self.switch_b, "cam")
        graph.add_edge(self.switch_port_b, self.router, "cam")
        graph.add_edge(self.switch_port_b, self.switch_a, "cam")
        graph.add_edge(self.router_port_a, self.switch_a, "cam")
        graph.add_edge(self.router_port_b, self.switch_b, "cam")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert result.has_edge(self.switch_port_a, self.router_port_a)
        assert result.has_edge(self.switch_port_b, self.router_port_b)
        assert result.has_edge(self.router_port_a, self.switch_port_a)
        assert result.has_edge(self.router_port_b, self.switch_port_b)
        assert result.out_degree(self.switch_port_a) == 1
        assert result.out_degree(self.switch_port_b) == 1
        assert result.out_degree(self.router_port_a) == 1
        assert result.out_degree(self.router_port_b) == 1

    def test_self_loop(self):
        graph = nx.MultiDiGraph(name="self loop")
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_port_a, self.switch_a, "cam")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert not result.has_edge(self.switch_port_a, self.switch_a)

    def test_no_return_path(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.switch_b, "cam")
        reducer = AdjacencyReducer(graph)
        print("input:")
        print(reducer.format_connections())
        reducer.reduce()
        print("result:")
        print(reducer.format_connections())
        result = reducer.graph
        assert result.has_edge(self.switch_port_a, self.switch_b)
        assert not result.has_edge(self.switch_port_b, self.switch_port_a)
        assert result.out_degree(self.switch_port_a) == 1
        assert self.switch_port_b not in result

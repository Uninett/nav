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

from types import SimpleNamespace

import networkx as nx
import pytest

from nav.topology.analyze import AdjacencyReducer, Box, Port
from nav.topology.stats import ReducerStats


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

    def test_when_lldp_pair_matches_then_stats_should_count_one_pair_matched(self):  # noqa: E501
        graph = nx.MultiDiGraph()
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.switch_port_b, "lldp")
        graph.add_edge(self.switch_port_b, self.switch_port_a, "lldp")
        stats = ReducerStats()
        reducer = AdjacencyReducer(graph, stats=stats)
        reducer.reduce()
        assert stats.lldp["pairs_matched"] == 1
        assert stats.lldp["unmatched_dropped"] == 0

    def test_when_lldp_edge_is_unmatched_then_stats_should_count_one_dropped(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.switch_port_b, "lldp")
        stats = ReducerStats()
        reducer = AdjacencyReducer(graph, stats=stats)
        reducer.reduce()
        assert stats.lldp["unmatched_dropped"] == 1
        assert stats.lldp["pairs_matched"] == 0

    def test_when_lldp_edge_is_self_loop_then_stats_should_count_one_self_loop(self):
        graph = nx.MultiDiGraph()
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_port_a, self.switch_port_a, "lldp")
        stats = ReducerStats()
        reducer = AdjacencyReducer(graph, stats=stats)
        reducer.reduce()
        assert stats.lldp["self_loops"] == 1

    def test_when_cam_resolves_via_single_dataless_then_stats_should_count_it(self):  # noqa: E501
        graph = nx.MultiDiGraph()
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_port_a, self.switch_b, "cam")
        stats = ReducerStats()
        reducer = AdjacencyReducer(graph, stats=stats)
        reducer.reduce()
        assert stats.cam["resolved_single_dataless"] == 1

    def test_when_cam_resolves_via_return_path_then_stats_should_count_it(self):
        graph = nx.MultiDiGraph(name="simple case cam")
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.switch_b, "cam")
        graph.add_edge(self.switch_port_b, self.switch_a, "cam")
        stats = ReducerStats()
        reducer = AdjacencyReducer(graph, stats=stats)
        reducer.reduce()
        assert stats.cam["resolved_return_path"] == 1

    def test_when_aggregate_is_removed_then_stats_should_count_one_removed(self):
        aggregator = Port((self.switch_a_id, 99))
        aggregator.name = "agg"
        graph = nx.MultiDiGraph()
        graph.add_edge(self.switch_a, aggregator)
        graph.add_edge(self.switch_a, self.switch_port_a)
        graph.add_edge(self.switch_b, self.switch_port_b)
        graph.add_edge(self.switch_port_a, self.switch_port_b, "lldp")
        graph.add_edge(self.switch_port_b, self.switch_port_a, "lldp")
        aggregates = {aggregator: {self.switch_port_a}}
        stats = ReducerStats()
        reducer = AdjacencyReducer(graph, aggregates=aggregates, stats=stats)
        reducer.reduce()
        assert stats.aggregates["removed"] == 1


class TestJuniperAggregateStackTransitivity:
    """Reproduces issue #4029: a Juniper aggregate (ae0) layered over
    logical units, which are in turn stacked above physical ports, must be
    suppressed once its physical members resolve via LLDP — even though the
    aggregate-to-physical relationship spans two hops through the stack.

    Topology modelled (all on the Juniper, netbox id 2):

        ae0                          aggregate (CAM-only, candidate is WRONG)
       /   \\
      u1    u2                       logical units (no candidate data)
      |      |
      p1    p2                       physical ports (LLDP to the real neighbor)

    p1/p2 resolve to the neighbor by LLDP. ae0's only candidate is a CAM
    entry pointing at an unrelated box. Before the fix, the one-hop member
    check in `_remove_aggregates` only sees {u1, u2} — neither of which is
    ever resolved — so ae0 survives into the CAM phase and is wrongly
    connected to the bystander.
    """

    def test_when_members_resolve_then_aggregate_should_not_inherit_cam_neighbor(
        self, reduced
    ):
        assert not reduced.result.has_edge(reduced.ae0, reduced.bystander)
        assert reduced.ae0 not in reduced.result

    def test_when_members_resolve_by_lldp_then_member_topology_should_stand(
        self, reduced
    ):
        assert reduced.result.has_edge(reduced.phys1, reduced.nbr_port1)
        assert reduced.result.has_edge(reduced.phys2, reduced.nbr_port2)

    def test_when_aggregate_suppressed_via_stack_then_stats_should_count_removed(
        self, reduced
    ):
        assert reduced.stats.aggregates["removed"] == 1

    def test_when_aggregate_is_three_layers_above_physical_then_it_should_be_suppressed(
        self,
    ):
        ae0 = _port(2, 100, "juniper (ae0)")
        unit = _port(2, 11, "juniper (xe-0/0/1.0)")
        mid = _port(2, 21, "juniper (xe-0/0/1 midstack)")
        phys = _port(2, 1, "juniper (xe-0/0/1)")
        aggregates = {ae0: {unit}, unit: {mid}, mid: {phys}}
        reduced = _reduce_single_member_scenario(aggregates)
        assert reduced.stats.aggregates["removed"] == 1
        assert reduced.ae0 not in reduced.result
        assert not reduced.result.has_edge(reduced.ae0, reduced.bystander)

    @pytest.mark.timeout(5)
    def test_when_aggregate_mapping_contains_cycle_then_suppression_terminates(self):
        ae0 = _port(2, 100, "juniper (ae0)")
        unit = _port(2, 11, "juniper (xe-0/0/1.0)")
        phys = _port(2, 1, "juniper (xe-0/0/1)")
        # The unit points back up to the aggregate, forming a cycle that the
        # member walk must not follow forever.
        aggregates = {ae0: {unit}, unit: {phys, ae0}}
        reduced = _reduce_single_member_scenario(aggregates)
        assert reduced.stats.aggregates["removed"] == 1
        assert reduced.ae0 not in reduced.result


@pytest.fixture
def reduced(juniper_aggregate_scenario):
    """Run the reducer over the scenario, exposing result graph, stats, and
    every scenario node as one namespace for terse assertions.
    """
    scenario = juniper_aggregate_scenario
    stats = ReducerStats()
    reducer = AdjacencyReducer(
        scenario.graph, aggregates=scenario.aggregates, stats=stats
    )
    reducer.reduce()
    return SimpleNamespace(result=reducer.graph, stats=stats, **vars(scenario))


@pytest.fixture
def juniper_aggregate_scenario():
    """Build the #4029 candidate graph plus its flat aggregate mapping.

    The mapping mirrors get_aggregate_mapping(include_stacks=True): the
    aggregate maps to its logical units, and each unit maps to its physical
    port — two hops from aggregate to physical member.
    """
    juniper = _box(2, "juniper")
    neighbor = _box(3, "neighbor")
    bystander = _box(1, "bystander")

    ae0 = _port(2, 100, "juniper (ae0)")
    unit1 = _port(2, 11, "juniper (xe-0/0/1.0)")
    unit2 = _port(2, 12, "juniper (xe-0/0/2.0)")
    phys1 = _port(2, 1, "juniper (xe-0/0/1)")
    phys2 = _port(2, 2, "juniper (xe-0/0/2)")
    nbr_port1 = _port(3, 1, "neighbor (xe-0/0/1)")
    nbr_port2 = _port(3, 2, "neighbor (xe-0/0/2)")

    aggregates = {
        ae0: {unit1, unit2},
        unit1: {phys1},
        unit2: {phys2},
    }

    graph = nx.MultiDiGraph(name="juniper aggregate stack")
    graph.add_edge(juniper, phys1)
    graph.add_edge(juniper, phys2)
    graph.add_edge(juniper, ae0)
    graph.add_edge(neighbor, nbr_port1)
    graph.add_edge(neighbor, nbr_port2)
    # Physical members have mutual LLDP with the real neighbor.
    graph.add_edge(phys1, nbr_port1, "lldp")
    graph.add_edge(nbr_port1, phys1, "lldp")
    graph.add_edge(phys2, nbr_port2, "lldp")
    graph.add_edge(nbr_port2, phys2, "lldp")
    # The aggregate's only evidence is a CAM entry to an unrelated box.
    graph.add_edge(ae0, bystander, "cam")

    return SimpleNamespace(
        graph=graph,
        aggregates=aggregates,
        ae0=ae0,
        bystander=bystander,
        phys1=phys1,
        phys2=phys2,
        nbr_port1=nbr_port1,
        nbr_port2=nbr_port2,
    )


def _reduce_single_member_scenario(aggregates):
    """Reduce the #4029 graph reduced to a single physical member.

    The graph is fixed — one aggregate (ae0) whose only candidate is a CAM
    entry to an unrelated box, and one physical port (xe-0/0/1) with mutual
    LLDP to a neighbor. The aggregate mapping is supplied by the caller so a
    test can vary its depth or introduce a cycle; any intermediate ports the
    mapping references but the graph omits stand in for the data-less logical
    units of a real stack.
    """
    juniper = _box(2, "juniper")
    neighbor = _box(3, "neighbor")
    bystander = _box(1, "bystander")
    ae0 = _port(2, 100, "juniper (ae0)")
    phys = _port(2, 1, "juniper (xe-0/0/1)")
    nbr_port = _port(3, 1, "neighbor (xe-0/0/1)")

    graph = nx.MultiDiGraph(name="single-member aggregate stack")
    graph.add_edge(juniper, phys)
    graph.add_edge(juniper, ae0)
    graph.add_edge(neighbor, nbr_port)
    graph.add_edge(phys, nbr_port, "lldp")
    graph.add_edge(nbr_port, phys, "lldp")
    graph.add_edge(ae0, bystander, "cam")

    stats = ReducerStats()
    reducer = AdjacencyReducer(graph, aggregates=aggregates, stats=stats)
    reducer.reduce()
    return SimpleNamespace(
        result=reducer.graph, stats=stats, ae0=ae0, phys=phys, bystander=bystander
    )


def _box(netbox_id, name):
    box = Box(netbox_id)
    box.name = name
    return box


def _port(netbox_id, interface_id, name):
    port = Port((netbox_id, interface_id))
    port.name = name
    return port

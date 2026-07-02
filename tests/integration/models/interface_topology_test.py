"""Tests for Interface.get_layered_topology and its aggregate/stack walk."""

from nav.models.manage import (
    BOTH_RELATION,
    InterfaceAggregate,
    InterfaceStack,
    LAG_RELATION,
    STACK_RELATION,
)


def _flatten(nodes):
    """Returns every node in the forest, depth-first (duplicates included)."""
    result = []
    for node in nodes:
        result.append(node)
        result.extend(_flatten(node.members))
    return result


def _find(nodes, ifname):
    """Returns the first node with the given ifname, depth-first."""
    for node in _flatten(nodes):
        if node.interface.ifname == ifname:
            return node
    return None


def _all_ifnames(nodes):
    """Returns every ifname in the forest, with duplicates (for back-references)."""
    return [node.interface.ifname for node in _flatten(nodes)]


def test_when_interface_has_no_layering_then_topology_should_be_a_single_self_root(
    netbox_factory, interface_factory
):
    box = netbox_factory("lonely.example.org", "10.1.0.1")
    iface = interface_factory(box, "GigabitEthernet1/0/1", 1)

    tree = iface.get_layered_topology()

    assert len(tree) == 1
    root = tree[0]
    assert root.interface == iface
    assert root.is_current
    assert root.relation is None
    assert root.members == []


def test_when_viewing_aggregate_then_members_should_nest_with_lag_and_stack_relations(
    juniper_aggregate_factory,
):
    topo = juniper_aggregate_factory()

    tree = topo["ae0"].get_layered_topology()

    assert len(tree) == 1, "ae0.0 should be suppressed as a redundant root"
    root = tree[0]
    assert root.interface == topo["ae0"]
    assert root.is_current

    units = {node.interface.ifname: node for node in root.members}
    assert set(units) == {"xe-0/2/2.0", "xe-0/2/3.0"}
    assert all(node.relation == LAG_RELATION for node in root.members)

    physical = units["xe-0/2/2.0"].members[0]
    assert physical.interface == topo["phys2"]
    assert physical.relation == STACK_RELATION
    assert physical.interface.to_netbox == topo["dist_a"]

    assert "ae0.0" not in _all_ifnames(tree)


def test_when_viewing_physical_member_then_root_should_be_the_aggregate(
    juniper_aggregate_factory,
):
    topo = juniper_aggregate_factory()

    tree = topo["phys2"].get_layered_topology()

    assert len(tree) == 1
    assert tree[0].interface == topo["ae0"]
    here = _find(tree, "xe-0/2/2")
    assert here.is_current
    assert "ae0.0" not in _all_ifnames(tree)


def test_when_viewing_logical_unit_then_it_should_not_be_suppressed(
    juniper_aggregate_factory,
):
    topo = juniper_aggregate_factory()

    tree = topo["ae0_0"].get_layered_topology()

    unit = _find(tree, "ae0.0")
    assert unit is not None
    assert unit.is_current


def test_when_member_is_bundled_and_stacked_by_parent_then_relation_should_be_both(
    juniper_aggregate_factory,
):
    topo = juniper_aggregate_factory()

    # ae0.0 both bundles (aggregate) and stacks above (stack) its units.
    tree = topo["ae0_0"].get_layered_topology()
    unit = _find(tree, "ae0.0")

    assert unit.members, "ae0.0 should list its members"
    assert all(member.relation == BOTH_RELATION for member in unit.members)
    # The tagging discriminates: the same tree also carries plain lag (ae0's
    # units) and stack (the physicals) edges, so it is not uniformly "both".
    relations = {node.relation for node in _flatten(tree) if node.relation}
    assert relations == {LAG_RELATION, STACK_RELATION, BOTH_RELATION}


def test_when_aggregate_carries_its_own_neighbour_then_the_link_should_be_on_its_node(
    juniper_aggregate_factory,
):
    topo = juniper_aggregate_factory()
    ae0 = topo["ae0"]
    ae0.to_netbox = topo["dist_a"]
    ae0.save()

    tree = ae0.get_layered_topology()

    assert tree[0].interface.to_netbox == topo["dist_a"]


def test_when_dag_re_reaches_a_node_then_only_one_occurrence_should_be_expanded(
    netbox_factory, interface_factory
):
    box = netbox_factory("dag.example.org", "10.2.0.1")
    ae0 = interface_factory(box, "ae0", 10)
    unit1 = interface_factory(box, "unit1", 20)
    unit2 = interface_factory(box, "unit2", 21)
    physical = interface_factory(box, "physical", 30)
    # ae0 bundles both units; unit1 stacks over unit2, unit2 over the physical.
    # So unit2 is reachable both directly under ae0 and under unit1, and the
    # walk must expand it exactly once and emit the other occurrence childless.
    InterfaceAggregate(aggregator=ae0, interface=unit1).save()
    InterfaceAggregate(aggregator=ae0, interface=unit2).save()
    InterfaceStack(higher=unit1, lower=unit2).save()
    InterfaceStack(higher=unit2, lower=physical).save()

    tree = ae0.get_layered_topology()

    assert tree[0].interface == ae0
    # physical is only reachable through unit2; appearing exactly once proves
    # unit2 was expanded a single time despite the two paths to it.
    assert _all_ifnames(tree).count("physical") == 1
    # unit2 appears twice; exactly one occurrence is expanded, the other is the
    # childless back-reference -- regardless of which path is walked first.
    unit2_nodes = [node for node in _flatten(tree) if node.interface == unit2]
    assert len(unit2_nodes) == 2
    expanded = [node for node in unit2_nodes if node.members]
    childless = [node for node in unit2_nodes if not node.members]
    assert len(expanded) == 1 and len(childless) == 1
    assert [m.interface for m in expanded[0].members] == [physical]


def test_when_stack_has_a_cycle_then_the_walk_should_terminate_and_stop_expanding(
    netbox_factory, interface_factory
):
    box = netbox_factory("cycle.example.org", "10.3.0.1")
    top = interface_factory(box, "top", 10)
    a = interface_factory(box, "a", 20)
    b = interface_factory(box, "b", 30)
    # top over a, then a<->b form a cycle below it.
    InterfaceStack(higher=top, lower=a).save()
    InterfaceStack(higher=a, lower=b).save()
    InterfaceStack(higher=b, lower=a).save()

    tree = top.get_layered_topology()  # must not raise / recurse forever

    root = tree[0]
    assert root.interface == top
    a_node = root.members[0]
    b_node = a_node.members[0]
    a_again = b_node.members[0]
    assert (a_node.interface, b_node.interface, a_again.interface) == (a, b, a)
    assert a_again.members == [], "the cycle guard should stop re-expansion"


def test_when_topology_built_then_members_should_be_ordered_by_ifindex(
    juniper_aggregate_factory,
):
    topo = juniper_aggregate_factory()

    members = topo["ae0"].get_layered_topology()[0].members

    ifindexes = [node.interface.ifindex for node in members]
    assert ifindexes == sorted(ifindexes)

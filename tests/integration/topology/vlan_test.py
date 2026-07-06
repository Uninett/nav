#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Integration tests for LAG-aware VLAN topology detection.

The topology detector records a Juniper aggregate's layer-2 neighbor on the
physical member ports, two stack layers below the ``ae`` interface, while the
802.1q configuration lives on the aggregate itself. These tests exercise the
whole VLAN pass (analyzer + database updater) to prove the two are bridged: the
detected VLAN lands on the aggregate, never on its physical members.
"""

from nav.models.manage import SwPortAllowedVlan, SwPortVlan, Vlan
from nav.topology import vlan as vlan_module
from nav.topology.vlan import VlanGraphAnalyzer, VlanTopologyUpdater

VLAN_NUMBER = 101


def test_when_uplink_is_aggregated_then_the_vlan_should_land_on_the_aggregate(
    juniper_aggregate_factory, interface_factory
):
    topo = _trunked_aggregate_topology(juniper_aggregate_factory, interface_factory)

    _detect_vlan_topology()

    assert SwPortVlan.objects.filter(interface=topo["ae0"]).exists()
    for member in ("phys2", "phys3", "unit2", "unit3"):
        assert not SwPortVlan.objects.filter(interface=topo[member]).exists(), (
            f"{topo[member].ifname} is a LAG member and must carry no swportvlan"
        )


def test_when_bearer_annotation_is_absent_then_the_aggregate_vlan_should_be_lost(
    juniper_aggregate_factory, interface_factory, monkeypatch
):
    """Without the aggregate/stack bridge the analyzer cannot see the VLAN on
    the member-keyed edge, so the aggregate is dropped. Guards against the fix
    being silently regressed."""
    topo = _trunked_aggregate_topology(juniper_aggregate_factory, interface_factory)
    monkeypatch.setattr(vlan_module, "annotate_vlan_bearers", lambda graph: None)

    _detect_vlan_topology()

    assert not SwPortVlan.objects.filter(interface=topo["ae0"]).exists()


def _detect_vlan_topology():
    analyzer = VlanGraphAnalyzer()
    analyzer.analyze_all()
    analyzer.add_access_port_vlans()
    VlanTopologyUpdater(analyzer.ifc_vlan_map)()


def _trunked_aggregate_topology(juniper_aggregate_factory, interface_factory):
    """Builds the aggregated-uplink scenario: ``ae0`` is a trunk carrying
    VLAN_NUMBER with its neighbor resolved on the physical members, and the far
    end has an access port on that VLAN so the DFS sees it as active.
    """
    topo = juniper_aggregate_factory()

    topo["ae0"].trunk = True
    topo["ae0"].save()
    allowed = SwPortAllowedVlan(interface=topo["ae0"])
    allowed.set_allowed_vlans([VLAN_NUMBER])
    allowed.save()

    access_port = interface_factory(topo["dist_a"], "ge-0/0/5", 5)
    access_port.vlan = VLAN_NUMBER
    access_port.save()

    Vlan(vlan=VLAN_NUMBER, net_type_id="lan", netbox=topo["sw"]).save()
    return topo

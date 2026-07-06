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
"""Unit tests for the aggregate/stack VLAN-bearer resolution in topology.vlan"""

from types import SimpleNamespace

import pytest

from nav.topology.vlan import (
    _ancestors,
    _carries_vlan_config,
    _find_bearer_pk,
)


class TestCarriesVlanConfig:
    def test_when_interface_is_none_then_it_should_return_false(self):
        assert _carries_vlan_config(None) is False

    def test_when_interface_is_a_trunk_then_it_should_return_true(self):
        assert _carries_vlan_config(_fake_interface(trunk=True)) is True

    def test_when_interface_has_an_access_vlan_then_it_should_return_true(self):
        assert _carries_vlan_config(_fake_interface(vlan=42)) is True

    def test_when_interface_has_allowed_vlans_but_no_trunk_then_it_should_return_false(
        self,
    ):
        # An allowed-VLAN set is only usable on a trunk, so on its own it does
        # not make an interface a VLAN bearer.
        assert (
            _carries_vlan_config(_fake_interface(swport_allowed_vlan=object())) is False
        )

    def test_when_interface_has_no_vlan_config_then_it_should_return_false(self):
        assert _carries_vlan_config(_fake_interface()) is False


class TestAncestors:
    def test_when_chain_is_linear_then_it_should_return_every_layer_above(self):
        parents = {1: {2}, 2: {3}}
        assert _ancestors(1, parents) == {2, 3}

    def test_when_interface_has_no_parents_then_it_should_return_empty_set(self):
        assert _ancestors(1, {}) == set()

    @pytest.mark.timeout(5)
    def test_when_hierarchy_has_a_cycle_then_it_should_terminate(self):
        # The timeout is the real assertion here: a lost cycle guard loops
        # forever, so without it a regression would hang rather than fail. The
        # returned set (which includes the seed, reached via the cycle) just
        # confirms the guard still computes the full closure.
        parents = {1: {2}, 2: {3}, 3: {1}}
        assert _ancestors(1, parents) == {1, 2, 3}


class TestFindBearerPk:
    def test_when_port_carries_its_own_config_then_it_should_be_its_own_bearer(self):
        config = {1: _fake_interface(trunk=True)}
        assert _find_bearer_pk(1, {}, config) == 1

    def test_when_no_layer_carries_config_then_it_should_fall_back_to_itself(self):
        parents = {1: {2}, 2: {3}}
        config = {1: _fake_interface(), 2: _fake_interface(), 3: _fake_interface()}
        assert _find_bearer_pk(1, parents, config) == 1

    def test_when_config_lives_two_layers_up_then_it_should_resolve_to_that_layer(self):
        # The Juniper case: physical -> logical unit -> aggregate (trunk config)
        parents = {1: {2}, 2: {3}}
        config = {
            1: _fake_interface(),
            2: _fake_interface(),
            3: _fake_interface(trunk=True, ifindex=865),
        }
        assert _find_bearer_pk(1, parents, config) == 3

    def test_when_two_layers_carry_config_then_it_should_pick_the_nearer(self):
        parents = {1: {2}, 2: {3}}
        config = {
            1: _fake_interface(),
            2: _fake_interface(trunk=True),
            3: _fake_interface(trunk=True),
        }
        assert _find_bearer_pk(1, parents, config) == 2

    def test_when_two_ancestors_in_a_layer_carry_config_then_it_should_pick_lowest_ifindex(  # noqa: E501
        self,
    ):
        # ae0 (ifindex 865) and its logical ae0.0 (876) both bundle the members;
        # only the lower ifIndex actually holds the configuration.
        parents = {1: {2}, 2: {3, 4}}
        config = {
            1: _fake_interface(),
            2: _fake_interface(),
            3: _fake_interface(trunk=True, ifindex=876),
            4: _fake_interface(trunk=True, ifindex=865),
        }
        assert _find_bearer_pk(1, parents, config) == 4


def _fake_interface(trunk=None, vlan=None, swport_allowed_vlan=None, ifindex=0):
    """A stand-in Interface for the pure bearer helpers, which only read plain
    attributes. A SimpleNamespace is chosen over a Mock on purpose: it holds
    real values, so the ``x or y`` / ``is None`` checks behave as they would on
    a real Interface, and it raises on any attribute the helper didn't expect
    rather than silently satisfying the check with a truthy auto-created Mock
    attribute.
    """
    return SimpleNamespace(
        trunk=trunk,
        vlan=vlan,
        swport_allowed_vlan=swport_allowed_vlan,
        ifindex=ifindex,
    )

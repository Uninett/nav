#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Tests for nav.ipdevpoll.utils module"""

from nav.ipdevpoll.utils import _workaround_broken_aruba_alternate_communities
from nav.mibs.types import LogicalMibInstance


class TestWorkaroundBrokenArubaAlternateCommunities:
    """Tests for _workaround_broken_aruba_alternate_communities()"""

    def test_should_append_vlan_index_when_missing(self):
        instances = [LogicalMibInstance(description="vlan100", community="public")]

        result = _workaround_broken_aruba_alternate_communities(instances)

        assert result[0].community == "public@100"

    def test_should_not_modify_when_already_indexed(self):
        instances = [LogicalMibInstance(description="vlan100", community="public@100")]

        result = _workaround_broken_aruba_alternate_communities(instances)

        assert result[0].community == "public@100"

    def test_should_preserve_context_fields(self):
        engine_id = bytes.fromhex("800000090300001234")
        instances = [
            LogicalMibInstance(
                description="vlan100",
                community="public",
                context="vlan-100",
                context_engine_id=engine_id,
            )
        ]

        result = _workaround_broken_aruba_alternate_communities(instances)

        assert result[0].community == "public@100"
        assert result[0].context == "vlan-100"
        assert result[0].context_engine_id == engine_id

    def test_should_not_modify_non_vlan_descriptions(self):
        instances = [LogicalMibInstance(description="bridge1", community="public")]

        result = _workaround_broken_aruba_alternate_communities(instances)

        assert result[0].community == "public"

    def test_should_handle_case_insensitive_vlan_names(self):
        instances = [
            LogicalMibInstance(description="VLAN200", community="public"),
            LogicalMibInstance(description="Vlan300", community="public"),
        ]

        result = _workaround_broken_aruba_alternate_communities(instances)

        assert result[0].community == "public@200"
        assert result[1].community == "public@300"

    def test_should_not_modify_when_community_is_none(self):
        instances = [LogicalMibInstance(description="vlan100", community=None)]

        result = _workaround_broken_aruba_alternate_communities(instances)

        assert result[0].community is None

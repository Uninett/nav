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
"""Tests for nav.mibs.types module"""

from nav.mibs.types import LogicalMibInstance


class TestLogicalMibInstance:
    """Tests for LogicalMibInstance NamedTuple"""

    def test_should_have_default_none_for_context(self):
        instance = LogicalMibInstance("vlan1", "public@1")
        assert instance.context is None

    def test_should_have_default_none_for_context_engine_id(self):
        instance = LogicalMibInstance("vlan1", "public@1")
        assert instance.context_engine_id is None

    def test_should_accept_context_parameter(self):
        instance = LogicalMibInstance("vlan1", "public@1", "vlan-1")
        assert instance.context == "vlan-1"

    def test_should_accept_context_engine_id_parameter(self):
        engine_id = bytes.fromhex("800000090300001234")
        instance = LogicalMibInstance("vlan1", "public@1", "vlan-1", engine_id)
        assert instance.context_engine_id == engine_id

    def test_should_be_hashable_for_set_operations(self):
        instance1 = LogicalMibInstance("vlan1", "public@1")
        instance2 = LogicalMibInstance("vlan1", "public@1")
        instance3 = LogicalMibInstance("vlan2", "public@2")

        instances = {instance1, instance2, instance3}
        assert len(instances) == 2

    def test_equal_instances_should_be_equal(self):
        instance1 = LogicalMibInstance("vlan1", "public@1", "ctx", None)
        instance2 = LogicalMibInstance("vlan1", "public@1", "ctx", None)
        assert instance1 == instance2

    def test_different_instances_should_not_be_equal(self):
        instance1 = LogicalMibInstance("vlan1", "public@1")
        instance2 = LogicalMibInstance("vlan2", "public@2")
        assert instance1 != instance2

    def test_can_access_fields_by_name(self):
        instance = LogicalMibInstance("desc", "comm", "ctx", b"\x00\x01")
        assert instance.description == "desc"
        assert instance.community == "comm"
        assert instance.context == "ctx"
        assert instance.context_engine_id == b"\x00\x01"

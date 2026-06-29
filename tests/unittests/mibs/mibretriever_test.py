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
"""Tests for nav.mibs.mibretriever module"""

from unittest.mock import Mock

from pynetsnmp.twistedsnmp import SnmpError
from twisted.internet.error import TimeoutError
from twisted.python.failure import Failure

from nav.ipdevpoll.snmp.common import SNMPParameters
from nav.mibs.mibretriever import MultiMibMixIn
from nav.mibs.types import LogicalMibInstance


def _make_failure(exception):
    """Wraps an exception in a Twisted Failure."""
    return Failure(exception)


class TestMultiMibMixInGetAlternateAgent:
    """Tests for MultiMibMixIn._get_alternate_agent()"""

    def test_should_use_community_for_snmpv2(self):
        agent = Mock()
        agent.community = "public"
        agent.ip = "10.0.0.1"
        agent.port = 161
        agent.snmp_parameters = SNMPParameters(version=2, community="public")

        mixin = MultiMibMixIn(agent, [])
        instance = LogicalMibInstance(
            description="vlan100", community="public@100", context="vlan-100"
        )

        alt_agent = mixin._get_alternate_agent(instance)

        assert alt_agent.snmp_parameters.community == "public@100"
        assert alt_agent.snmp_parameters.context_name is None

    def test_should_use_context_for_snmpv3(self):
        agent = Mock()
        agent.community = "public"
        agent.ip = "10.0.0.1"
        agent.port = 161
        agent.snmp_parameters = SNMPParameters(version=3, sec_name="user")

        mixin = MultiMibMixIn(agent, [])
        instance = LogicalMibInstance(
            description="vlan100", community="public@100", context="vlan-100"
        )

        alt_agent = mixin._get_alternate_agent(instance)

        assert alt_agent.snmp_parameters.context_name == "vlan-100"
        # community should remain unchanged for v3
        assert alt_agent.snmp_parameters.community == "public"

    def test_should_include_context_engine_id_for_snmpv3_when_provided(self):
        agent = Mock()
        agent.community = "public"
        agent.ip = "10.0.0.1"
        agent.port = 161
        agent.snmp_parameters = SNMPParameters(version=3, sec_name="user")

        mixin = MultiMibMixIn(agent, [])
        engine_id = bytes.fromhex("800000090300001234")
        instance = LogicalMibInstance(
            description="vlan100",
            community="public@100",
            context="vlan-100",
            context_engine_id=engine_id,
        )

        alt_agent = mixin._get_alternate_agent(instance)

        assert alt_agent.snmp_parameters.context_engine_id == "800000090300001234"

    def test_should_not_include_context_engine_id_when_not_provided(self):
        agent = Mock()
        agent.community = "public"
        agent.ip = "10.0.0.1"
        agent.port = 161
        agent.snmp_parameters = SNMPParameters(version=3, sec_name="user")

        mixin = MultiMibMixIn(agent, [])
        instance = LogicalMibInstance(
            description="vlan100", community="public@100", context="vlan-100"
        )

        alt_agent = mixin._get_alternate_agent(instance)

        assert alt_agent.snmp_parameters.context_engine_id is None

    def test_should_copy_protocol_from_base_agent(self):
        agent = Mock()
        agent.community = "public"
        agent.ip = "10.0.0.1"
        agent.port = 161
        agent.protocol = Mock()
        agent.snmp_parameters = SNMPParameters(version=2, community="public")

        mixin = MultiMibMixIn(agent, [])
        instance = LogicalMibInstance(description="vlan100", community="public@100")

        alt_agent = mixin._get_alternate_agent(instance)

        assert alt_agent.protocol is agent.protocol


class TestMultiMibMixInTimeoutHandler:
    """Tests for MultiMibMixIn.__timeout_handler()"""

    def _make_mixin(self):
        agent = Mock()
        agent.community = "public"
        agent.ip = "10.0.0.1"
        agent.port = 161
        agent.snmp_parameters = SNMPParameters(version=2, community="public")
        return MultiMibMixIn(agent, [])

    def _handle(self, mixin, failure, descr="vlan100"):
        # __timeout_handler is name-mangled
        return mixin._MultiMibMixIn__timeout_handler(failure, descr)

    def test_when_alternate_instance_returns_snmp_error_then_it_should_be_ignored(self):
        mixin = self._make_mixin()
        mixin.agent_proxy = Mock()  # any non-base agent
        failure = _make_failure(
            SnmpError("Packet for 10.0.0.1 has error: Permission denied")
        )

        assert self._handle(mixin, failure) is None

    def test_when_alternate_instance_times_out_then_it_should_be_ignored(self):
        mixin = self._make_mixin()
        mixin.agent_proxy = Mock()  # any non-base agent
        failure = _make_failure(TimeoutError("timed out"))

        assert self._handle(mixin, failure) is None

    def test_when_base_instance_returns_snmp_error_then_it_should_propagate(self):
        mixin = self._make_mixin()
        # agent_proxy is left as the base agent
        failure = _make_failure(SnmpError("Packet for 10.0.0.1 has error: genErr"))

        assert self._handle(mixin, failure, descr=None) is failure

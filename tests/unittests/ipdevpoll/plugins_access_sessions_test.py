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
"""Unit tests for the vendor-neutral access session plugin base"""

from configparser import ConfigParser
from unittest.mock import Mock, patch

import pytest
from twisted.internet import defer

from nav.ipdevpoll import shadows
from nav.ipdevpoll.plugins.access_sessions import (
    AccessSessionsPlugin,
    CollectedSession,
    valid_vlan_or_none,
)
from nav.ipdevpoll.shadows.access_session import make_session_key
from nav.ipdevpoll.storage import ContainerRepository
from nav.models.manage import InterfaceAccessSession as Session

KNOWN_IFINDEX = 10101
UNKNOWN_IFINDEX = 99999
SESSION_ID = b"\x0a\x00\x00\x01\xab"
FAKE_VENDOR_ID = 12345


class TestHandle:
    @pytest.mark.twisted
    async def test_when_session_is_collected_then_it_should_create_a_container(self):
        plugin = await _run_plugin([_collected()])

        session = _only_session(plugin)
        assert session.session_key == make_session_key(SESSION_ID)
        assert session.interface.ifindex == KNOWN_IFINDEX
        assert session.vlan_tag == 330
        assert session.status == Session.STATUS_AUTHORIZED
        assert session.domain == Session.DOMAIN_DATA
        assert session.method == Session.METHOD_DOT1X

    @pytest.mark.twisted
    async def test_when_session_is_on_unknown_ifindex_then_session_should_be_skipped(
        self,
    ):
        plugin = await _run_plugin([_collected(ifindex=UNKNOWN_IFINDEX)])

        assert plugin.containers[shadows.InterfaceAccessSession] == {}

    @pytest.mark.twisted
    async def test_when_no_sessions_are_collected_then_it_should_still_add_the_shadow(
        self,
    ):
        plugin = await _run_plugin([])

        assert shadows.InterfaceAccessSession in plugin.containers

    @pytest.mark.twisted
    async def test_when_vlan_tag_is_invalid_then_it_should_store_no_vlan(self):
        plugin = await _run_plugin([_collected(vlan_tag=0)])

        assert _only_session(plugin).vlan_tag is None

    @pytest.mark.twisted
    async def test_when_identity_is_not_collected_then_identity_should_be_cleared(self):
        plugin = await _run_plugin([_collected_with_identity()])

        assert plugin.collect_sessions_args == [False]
        session = _only_session(plugin)
        assert (session.client_mac, session.username) == (None, None)
        assert {"client_mac", "username"} <= set(session.get_touched())

    @pytest.mark.twisted
    async def test_when_identity_is_collected_then_identity_should_be_stored(self):
        plugin = await _run_plugin(
            [_collected_with_identity()], collect_client_identity=True
        )

        assert plugin.collect_sessions_args == [True]
        session = _only_session(plugin)
        assert (session.client_mac, session.username) == ("00:11:22:aa:bb:cc", "alice")


class TestSubclassing:
    def test_when_subclass_has_no_vendor_restriction_then_it_should_be_rejected(self):
        with pytest.raises(TypeError):

            class _Unrestricted(AccessSessionsPlugin):
                pass

    def test_when_class_has_no_vendor_restriction_then_can_handle_should_return_false(
        self,
    ):
        assert not AccessSessionsPlugin.can_handle(Mock())


class TestOnPluginLoad:
    @pytest.mark.parametrize("value, expected", [("yes", True), ("no", False)])
    def test_when_option_is_configured_then_it_should_set_collect_client_identity(
        self, value, expected
    ):
        config = ConfigParser()
        config.read_string(f"[access_sessions]\ncollect_client_identity = {value}\n")

        with (
            patch("nav.ipdevpoll.config.ipdevpoll_conf", config),
            patch.object(_FakeVendorSessions, "collect_client_identity", None),
        ):
            _FakeVendorSessions.on_plugin_load()

            assert _FakeVendorSessions.collect_client_identity is expected

    def test_when_option_is_missing_then_it_should_not_collect_client_identity(self):
        with (
            patch("nav.ipdevpoll.config.ipdevpoll_conf", ConfigParser()),
            patch.object(_FakeVendorSessions, "collect_client_identity", None),
        ):
            _FakeVendorSessions.on_plugin_load()

            assert _FakeVendorSessions.collect_client_identity is False


class TestValidVlanOrNone:
    @pytest.mark.parametrize("vlan", [1, 330, 4094])
    def test_when_vlan_is_in_range_then_it_should_return_it(self, vlan):
        assert valid_vlan_or_none(vlan) == vlan

    @pytest.mark.parametrize("vlan", [0, 4095, None, "330"])
    def test_when_vlan_is_not_a_valid_tag_then_it_should_return_none(self, vlan):
        assert valid_vlan_or_none(vlan) is None


class _FakeVendorSessions(AccessSessionsPlugin):
    """Returns a canned list of sessions, and records how it was asked"""

    RESTRICT_TO_VENDORS = [FAKE_VENDOR_ID]

    def __init__(self, *args, sessions=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.canned_sessions = list(sessions)
        self.collect_sessions_args = []

    async def collect_sessions(self, include_identity):
        self.collect_sessions_args.append(include_identity)
        return self.canned_sessions


async def _run_plugin(sessions, collect_client_identity=False):
    plugin = _FakeVendorSessions(
        Mock(id=1), Mock(), ContainerRepository(), sessions=sessions
    )
    plugin.collect_client_identity = collect_client_identity
    with patch(
        "nav.ipdevpoll.plugins.access_sessions.db.run_in_thread",
        side_effect=lambda func, ifindexes: defer.succeed(ifindexes & {KNOWN_IFINDEX}),
    ):
        await plugin.handle()
    return plugin


def _only_session(plugin):
    (session,) = plugin.containers[shadows.InterfaceAccessSession].values()
    return session


def _collected(**overrides):
    fields = dict(
        ifindex=KNOWN_IFINDEX,
        session_id=SESSION_ID,
        vlan_tag=330,
        method=Session.METHOD_DOT1X,
        domain=Session.DOMAIN_DATA,
        status=Session.STATUS_AUTHORIZED,
    )
    return CollectedSession(**{**fields, **overrides})


def _collected_with_identity():
    return _collected(client_mac="00:11:22:aa:bb:cc", username="alice")

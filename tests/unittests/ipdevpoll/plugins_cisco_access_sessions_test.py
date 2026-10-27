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
"""Unit tests for the cisco_access_sessions ipdevpoll plugin"""

from unittest.mock import Mock, patch

import pytest
from twisted.internet import defer

from nav.ipdevpoll.plugins.access_sessions import CollectedSession
from nav.ipdevpoll.plugins.cisco_access_sessions import (
    CiscoAccessSessions,
    select_method,
    to_collected_session,
)
from nav.models.manage import InterfaceAccessSession as Session

IFINDEX = 10101
SESSION_ID = b"\x0a\x00\x00\x01\xab"
MAC_OCTETS = b"\x00\x11\x22\xaa\xbb\xcc"


class TestCollectSessions:
    @pytest.mark.twisted
    async def test_when_sessions_are_found_then_it_should_convert_them(self):
        sessions, _mib = await _collect({(IFINDEX, SESSION_ID): _row()})

        assert sessions == [
            CollectedSession(
                ifindex=IFINDEX,
                session_id=SESSION_ID,
                vlan_tag=330,
                method=Session.METHOD_DOT1X,
                domain=Session.DOMAIN_DATA,
                status=Session.STATUS_AUTHORIZED,
            )
        ]

    @pytest.mark.twisted
    async def test_when_no_sessions_are_found_then_it_should_not_fetch_methods(self):
        sessions, mib = await _collect({})

        assert sessions == []
        mib.get_session_methods.assert_not_called()

    @pytest.mark.twisted
    @pytest.mark.parametrize("include_identity", [True, False])
    async def test_when_asked_for_identity_then_it_should_pass_that_on_to_the_mib(
        self, include_identity
    ):
        _sessions, mib = await _collect({}, include_identity=include_identity)

        mib.get_sessions.assert_called_once_with(include_identity=include_identity)


class TestToCollectedSession:
    def test_when_row_has_identity_then_it_should_format_it(self):
        row = _row(
            cafSessionClientMacAddress=MAC_OCTETS, cafSessionAuthUserName="alice"
        )

        session = to_collected_session((IFINDEX, SESSION_ID), row, {})

        assert (session.client_mac, session.username) == ("00:11:22:aa:bb:cc", "alice")

    @pytest.mark.parametrize(
        "status, expected",
        [
            ("idle", Session.STATUS_PENDING),
            ("running", Session.STATUS_PENDING),
            ("noMethod", Session.STATUS_AUTHENTICATION_FAILED),
            ("authenticationSuccess", Session.STATUS_AUTHENTICATED),
            ("authenticationFailed", Session.STATUS_AUTHENTICATION_FAILED),
            ("authorizationSuccess", Session.STATUS_AUTHORIZED),
            ("authorizationFailed", Session.STATUS_AUTHORIZATION_FAILED),
            (None, Session.STATUS_UNKNOWN),
        ],
    )
    def test_when_status_is_given_then_it_should_map_it(self, status, expected):
        session = to_collected_session(
            (IFINDEX, SESSION_ID), _row(cafSessionStatus=status), {}
        )

        assert session.status == expected

    @pytest.mark.parametrize(
        "domain, expected",
        [
            ("data", Session.DOMAIN_DATA),
            ("voice", Session.DOMAIN_VOICE),
            ("other", Session.DOMAIN_UNKNOWN),
        ],
    )
    def test_when_domain_is_given_then_it_should_map_it(self, domain, expected):
        session = to_collected_session(
            (IFINDEX, SESSION_ID), _row(cafSessionDomain=domain), {}
        )

        assert session.domain == expected


class TestSelectMethod:
    @pytest.mark.parametrize(
        "method_states, expected",
        [
            ({"dot1x": "authcFailed", "macAuthBypass": "authcSuccess"}, "mab"),
            ({"dot1x": "running", "macAuthBypass": "notRun"}, "dot1x"),
            ({"webAuth": "authcFailed"}, "webauth"),
            ({"dot1x": "authcFailed", "macAuthBypass": "authcFailed"}, "unknown"),
            ({"dot1x": "failedOver", "macAuthBypass": "authcFailed"}, "mab"),
            ({"dot1x": "notRun"}, "unknown"),
            ({"other": "authcSuccess"}, "unknown"),
            ({}, "unknown"),
        ],
    )
    def test_when_given_method_states_then_it_should_select_expected_method(
        self, method_states, expected
    ):
        assert select_method(method_states) == expected


async def _collect(sessions, include_identity=False):
    plugin = CiscoAccessSessions(Mock(), Mock(), Mock())
    mib = Mock()
    mib.get_sessions.return_value = defer.succeed(sessions)
    mib.get_session_methods.return_value = defer.succeed(
        {key: {"dot1x": "authcSuccess"} for key in sessions}
    )
    with patch(
        "nav.ipdevpoll.plugins.cisco_access_sessions.CiscoAuthFrameworkMib",
        return_value=mib,
    ):
        result = await plugin.collect_sessions(include_identity)
    return result, mib


def _row(**overrides):
    return {
        "cafSessionStatus": "authorizationSuccess",
        "cafSessionDomain": "data",
        "cafSessionAuthVlan": 330,
        **overrides,
    }

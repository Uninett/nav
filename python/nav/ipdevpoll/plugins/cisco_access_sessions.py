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
"""Collects client authentication sessions (802.1X, MAB, web auth) from Cisco
switches, including any VLANs they were dynamically assigned.
"""

from typing import Any

from nav.enterprise.ids import VENDOR_ID_CISCOSYSTEMS
from nav.ipdevpoll.plugins.access_sessions import (
    AccessSessionsPlugin,
    CollectedSession,
)
from nav.ipdevpoll.utils import binary_mac_to_hex
from nav.mibs.cisco_auth_framework_mib import CiscoAuthFrameworkMib, SessionIndex
from nav.models import manage

Session = manage.InterfaceAccessSession

STATUS_MAP = {
    "idle": Session.STATUS_PENDING,
    "running": Session.STATUS_PENDING,
    # No method produced a result, so the client was never authenticated
    "noMethod": Session.STATUS_AUTHENTICATION_FAILED,
    "authenticationSuccess": Session.STATUS_AUTHENTICATED,
    "authenticationFailed": Session.STATUS_AUTHENTICATION_FAILED,
    "authorizationSuccess": Session.STATUS_AUTHORIZED,
    "authorizationFailed": Session.STATUS_AUTHORIZATION_FAILED,
}
DOMAIN_MAP = {
    "data": Session.DOMAIN_DATA,
    "voice": Session.DOMAIN_VOICE,
}
METHOD_MAP = {
    "dot1x": Session.METHOD_DOT1X,
    "macAuthBypass": Session.METHOD_MAB,
    "webAuth": Session.METHOD_WEBAUTH,
}
METHOD_STATE_PRECEDENCE = ("authcSuccess", "running", "authcFailed")


class CiscoAccessSessions(AccessSessionsPlugin):
    """Collects authentication sessions from CISCO-AUTH-FRAMEWORK-MIB"""

    RESTRICT_TO_VENDORS = [VENDOR_ID_CISCOSYSTEMS]

    async def collect_sessions(self, include_identity: bool) -> list[CollectedSession]:
        mib = CiscoAuthFrameworkMib(self.agent)
        sessions = await mib.get_sessions(include_identity=include_identity)
        if not sessions:
            return []
        methods = await mib.get_session_methods()
        return [
            to_collected_session(index, row, methods.get(index, {}))
            for index, row in sessions.items()
        ]


def to_collected_session(
    index: SessionIndex, row: dict[str, Any], method_states: dict[str, str]
) -> CollectedSession:
    """Converts a cafSessionTable row to a vendor-neutral session"""
    ifindex, session_id = index
    return CollectedSession(
        ifindex=ifindex,
        session_id=session_id,
        vlan_tag=row.get("cafSessionAuthVlan"),
        method=select_method(method_states),
        domain=DOMAIN_MAP.get(row.get("cafSessionDomain"), Session.DOMAIN_UNKNOWN),
        status=STATUS_MAP.get(row.get("cafSessionStatus"), Session.STATUS_UNKNOWN),
        client_mac=binary_mac_to_hex(row.get("cafSessionClientMacAddress")),
        username=row.get("cafSessionAuthUserName") or None,
    )


def select_method(method_states: dict[str, str]) -> str:
    """Selects which of the methods tried for a session it is attributed to.

    A method that succeeded wins over one still running, which wins over one
    that failed.  Methods that were not run, or that failed over to another
    method, never decide the outcome.  If several methods share the deciding
    state, the method is unknown.
    """
    for wanted_state in METHOD_STATE_PRECEDENCE:
        matches = [m for m, state in method_states.items() if state == wanted_state]
        if len(matches) == 1:
            return METHOD_MAP.get(matches[0], Session.METHOD_UNKNOWN)
        if matches:
            return Session.METHOD_UNKNOWN
    return Session.METHOD_UNKNOWN

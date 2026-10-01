#
# Copyright (C) 2025 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""CISCO-AUTH-FRAMEWORK-MIB handling

This module provides a MibRetriever for querying authentication sessions
on Cisco devices using the CISCO-AUTH-FRAMEWORK-MIB.
"""

from collections import defaultdict
from typing import Any

from nav.smidumps import get_mib
from nav.mibs import mibretriever

SessionIndex = tuple[int, bytes]

SESSION_COLUMNS = ['cafSessionStatus', 'cafSessionDomain', 'cafSessionAuthVlan']
IDENTITY_COLUMNS = ['cafSessionClientMacAddress', 'cafSessionAuthUserName']


class CiscoAuthFrameworkMib(mibretriever.MibRetriever):
    """MIB retriever for CISCO-AUTH-FRAMEWORK-MIB"""

    mib = get_mib('CISCO-AUTH-FRAMEWORK-MIB')

    async def get_sessions(
        self, include_identity: bool = False
    ) -> dict[SessionIndex, dict[str, Any]]:
        """Retrieves the authentication sessions from cafSessionTable.

        Enumerated values are translated to their names.  The identifying
        columns (client MAC address and user name) are only retrieved when
        `include_identity` is true.

        :returns: A dict mapping (ifIndex, session id) to a dict of column values.
        """
        columns = SESSION_COLUMNS + (IDENTITY_COLUMNS if include_identity else [])
        rows = self.translate_result(await self.retrieve_columns(columns))
        result = {}
        for index, row in rows.items():
            try:
                session_index = _decode_session_index(index)
            except (ValueError, IndexError):
                self._logger.warning("ignoring malformed session index %r", index)
                continue
            # MibTableResultRow also keeps the row index under the key 0
            result[session_index] = {
                column: value for column, value in row.items() if column != 0
            }
        return result

    async def get_session_methods(self) -> dict[SessionIndex, dict[str, str]]:
        """Retrieves the state of each authentication method tried per session.

        :returns: A dict mapping (ifIndex, session id) to a dict of
                  method name -> method state name.
        """
        states = await self.retrieve_column('cafSessionMethodState')
        method_node = self.nodes['cafSessionMethod']
        state_node = self.nodes['cafSessionMethodState']
        result = defaultdict(dict)
        for index, state in states.items():
            try:
                session_index, method = _decode_method_index(index)
            except (ValueError, IndexError):
                self._logger.warning("ignoring malformed method index %r", index)
                continue
            method_name = method_node.to_python(method)
            result[session_index][method_name] = state_node.to_python(state)
        return dict(result)

    async def get_auth_session_vlans(self) -> dict[tuple[int, ...], dict[str, Any]]:
        """Retrieves VLAN information for authentication sessions.

        Queries cafSessionAuthVlan to get active authentication sessions
        and their assigned VLANs. This is useful for investigating 802.1X
        and MAC Authentication Bypass (MAB) behavior.

        Returns:
            A dictionary mapping (ifIndex, sessionId, ...) tuples to session
            data dictionaries containing cafSessionAuthVlan values.
            Example: {(10101, 'sessionid'...): {'cafSessionAuthVlan': 10}}
        """
        sessions = await self.retrieve_columns(['cafSessionAuthVlan'])
        return sessions


def _decode_session_index(index: tuple[int, ...]) -> SessionIndex:
    """Decodes a cafSessionEntry index, where the session id is IMPLIED (its
    octets follow the ifIndex without a length prefix).

    :raises ValueError: if the index is malformed.
    """
    if len(index) < 2:
        raise ValueError(f"no session id in index {index!r}")
    return index[0], bytes(index[1:])


def _decode_method_index(index: tuple[int, ...]) -> tuple[SessionIndex, int]:
    """Decodes a cafSessionMethodsInfoEntry index, where the session id is
    length-prefixed and followed by the method number.

    :raises ValueError: if the index is malformed.
    """
    ifindex, length = index[0], index[1]
    if len(index) != length + 3:
        raise ValueError(f"length prefix doesn't match index {index!r}")
    session_id = bytes(index[2 : 2 + length])
    return (ifindex, session_id), index[2 + length]

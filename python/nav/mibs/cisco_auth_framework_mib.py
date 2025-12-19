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

from typing import Any

from nav.smidumps import get_mib
from nav.mibs import mibretriever


class CiscoAuthFrameworkMib(mibretriever.MibRetriever):
    """MIB retriever for CISCO-AUTH-FRAMEWORK-MIB"""

    mib = get_mib('CISCO-AUTH-FRAMEWORK-MIB')

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

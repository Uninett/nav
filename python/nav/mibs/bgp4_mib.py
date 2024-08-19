#
# Copyright (C) 2017 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Implements a BGP4-MIB MibRetriever and associated functionality."""

from collections import namedtuple
from pprint import pformat
import logging

from twisted.internet import defer

from nav.oidparsers import oid_to_ipv4
from nav.smidumps import get_mib
from . import mibretriever

BgpPeerState = namedtuple('BgpPeerState', 'peer state adminstatus local_as remote_as')


class BGP4Mib(mibretriever.MibRetriever):
    """MibRetriever implementation for BGP4-MIB"""

    mib = get_mib('BGP4-MIB')
    SUPPORTED_ROOT = 'bgp'
    PEERSTATE_COLUMN = 'bgpPeerState'
    ADMINSTATUS_COLUMN = 'bgpPeerAdminStatus'
    LOCAL_AS_COLUMN = None
    REMOTE_AS_COLUMN = 'bgpPeerRemoteAs'
    GLOBAL_LOCAL_AS = 'bgpLocalAs'

    @defer.inlineCallbacks
    def is_supported(self):
        """Verifies whether any part of this MIB is supported by this device.

        :returns: A Deferred containing a boolean result.

        """
        reply = yield self.get_next(self.SUPPORTED_ROOT)
        return bool(reply)

    @defer.inlineCallbacks
    def get_bgp_peer_states(self):
        """Collects the table of BGP peering sessions.

        :returns: A Deferred whose positive result is a list of BgpPeerState
                  namedtuples.

        """
        if self.LOCAL_AS_COLUMN:
            columns = (
                self.PEERSTATE_COLUMN,
                self.ADMINSTATUS_COLUMN,
                self.LOCAL_AS_COLUMN,
                self.REMOTE_AS_COLUMN,
            )
            local_as = None
        else:
            columns = (
                self.PEERSTATE_COLUMN,
                self.ADMINSTATUS_COLUMN,
                self.REMOTE_AS_COLUMN,
            )
            local_as = yield self.get_next(self.GLOBAL_LOCAL_AS)
            self._logger.debug("local AS number: %r", local_as)

        rows = yield self.retrieve_columns(columns).addCallback(self.translate_result)
        result = {
            self._bgp_row_to_remote_ip(key): BgpPeerState(
                self._bgp_row_to_remote_ip(key),
                row[self.PEERSTATE_COLUMN],
                row[self.ADMINSTATUS_COLUMN],
                (row[self.LOCAL_AS_COLUMN] if self.LOCAL_AS_COLUMN else local_as),
                row[self.REMOTE_AS_COLUMN],
            )
            for key, row in rows.items()
        }

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("Found BGP peers:\n%s", pformat(result))
        return result

    @staticmethod
    def _bgp_row_to_remote_ip(row_index):
        return oid_to_ipv4(row_index)

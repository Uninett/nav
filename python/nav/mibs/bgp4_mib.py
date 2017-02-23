#
# Copyright (C) 2017 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Implements a BGP4-MIB MibRetriever and associated functionality."""

from __future__ import absolute_import
from twisted.internet import defer
from twisted.internet.defer import returnValue

from collections import namedtuple
from nav.oidparsers import oid_to_ipv4
from . import mibretriever

BgpPeerState = namedtuple('BgpPeerState', 'peer state adminstatus')


class BGP4Mib(mibretriever.MibRetriever):
    """MibRetriever implementation for BGP4-MIB"""
    from nav.smidumps.bgp4_mib import MIB as mib
    ROOT = 'bgp'

    @defer.inlineCallbacks
    def is_supported(self):
        """Verifies whether any part of this MIB is supported by this device.

        :returns: A Deferred containing a boolean result.

        """
        reply = yield self.get_next(self.ROOT)
        returnValue(bool(reply))

    @defer.inlineCallbacks
    def get_bgp_peer_states(self):
        """Collects the table of BGP peering sessions.

        :returns: A Deferred whose positive result is a list of BgpPeerState
                  namedtuples.

        """
        states = yield self.retrieve_columns(
            ['bgpPeerState', 'bgpPeerAdminStatus']
        ).addCallback(self.translate_result)
        result = {oid_to_ipv4(key): BgpPeerState(oid_to_ipv4(key),
                                                 row['bgpPeerState'],
                                                 row['bgpPeerAdminStatus'])
                  for key, row in states.iteritems()}
        returnValue(result)

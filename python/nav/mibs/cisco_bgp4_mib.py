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
#
"""Implements a CISCO-BGP4-MIB MibRetriever w/associated functionality."""

from __future__ import absolute_import
from twisted.internet import defer
from twisted.internet.defer import returnValue

from nav.oidparsers import consume, TypedInetAddress
from .bgp4_mib import BGP4Mib, BgpPeerState


class CiscoBGP4Mib(BGP4Mib):
    """MibRetriever implementation for CISCO-BGP4-MIB"""
    from nav.smidumps.cisco_bgp4_mib import MIB as mib
    ROOT = 'cbgpPeer2Table'

    @defer.inlineCallbacks
    def get_bgp_peer_states(self):
        """Collects the table of BGP peering sessions.

        :returns: A Deferred whose positive result is a list of BgpPeerState
                  namedtuples.

        """
        states = yield self.retrieve_columns(
            ['cbgpPeer2State', 'cbgpPeer2AdminStatus']
        ).addCallback(self.translate_result)
        result = {_get_remote_ip_address(key):
                  BgpPeerState(_get_remote_ip_address(key),
                               row['cbgpPeer2State'],
                               row['cbgpPeer2AdminStatus'])
                  for key, row in states.iteritems()}
        returnValue(result)


def _get_remote_ip_address(oid):
    remote_addr, = consume(oid, TypedInetAddress)
    return remote_addr

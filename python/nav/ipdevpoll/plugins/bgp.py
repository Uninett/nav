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
"""BGP peer state monitor plugin for ipdevpoll"""
from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.mibs.bgp4_mib import BGP4Mib
from nav.ipdevpoll.shadows import GatewayPeerSession, Netbox
from nav.models import manage


class BGP(Plugin):
    """Monitors the state of BGP peers through polling"""

    @classmethod
    def can_handle(cls, netbox):
        """This will only be useful on routers"""
        daddy_says_ok = super(BGP, cls).can_handle(netbox)
        return daddy_says_ok and netbox.category.id in ('GW', 'GSW')

    @defer.inlineCallbacks
    def handle(self):
        mib = BGP4Mib(self.agent)
        data = yield mib.get_bgp_peer_states()
        for peer in data.values():
            if str(peer.peer) == '0.0.0.0':
                self._logger.debug("ignoring buggy bgp entry: %r", peer)
                continue  # ignore buggy entries
            else:
                self._logger.debug("bgp peer: %r", peer)
            self._make_gwpeer(peer)

    def _make_gwpeer(self, bgp_peer_state):
        netbox = self.containers.factory(None, Netbox)

        key = ('bgp', str(bgp_peer_state.peer))
        session = self.containers.factory(key, GatewayPeerSession)
        session.netbox = self.netbox
        session.protocol = manage.GatewayPeerSession.PROTOCOL_BGP
        session.peer = bgp_peer_state.peer
        session.state = bgp_peer_state.state
        session.adminstatus = bgp_peer_state.adminstatus

        return session

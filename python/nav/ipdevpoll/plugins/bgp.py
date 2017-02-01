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
            self._logger.debug("bgp peer: %r", peer)

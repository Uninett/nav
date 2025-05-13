#
# Copyright (C) 2011,2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Collects interface link states and dispatches NAV events on changes"""

from twisted.internet.defer import inlineCallbacks

from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows


class LinkState(Plugin):
    """Monitors interface link states"""

    @inlineCallbacks
    def handle(self):
        if self.netbox.master:
            self._logger.debug(
                "this is a virtual instance of %s, not polling", self.netbox.master
            )
            return None

        ifmib = IfMib(self.agent)
        result = yield ifmib.retrieve_columns(
            ['ifName', 'ifAdminStatus', 'ifOperStatus']
        ).addCallback(reduce_index)
        self._put_results(result)

    def _put_results(self, results):
        netbox = self.containers.factory(None, shadows.Netbox)
        for index, row in results.items():
            if isinstance(index, int):  # only accept proper ifIndex values
                self._update_interface(netbox, index, row)

    def _update_interface(self, netbox, ifindex, row):
        ifc = self.containers.factory(ifindex, shadows.Interface)
        ifc.netbox = netbox
        ifc.ifindex = ifindex
        if row['ifName']:
            ifc.ifname = row['ifName']
        ifc.ifadminstatus = row['ifAdminStatus']
        ifc.ifoperstatus = row['ifOperStatus']

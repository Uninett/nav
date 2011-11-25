#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Collects interface link states and dispatches NAV events on changes"""

from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib

from nav.models.manage import Interface

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

class LinkState(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self.ifmib = IfMib(self.agent)
        df = self.ifmib.retrieve_columns(['ifName', 'ifOperStatus'])
        df.addCallback(reduce_index)
        return df.addCallback(self._put_results)

    def _put_results(self, results):
        netbox = self.containers.factory(None, shadows.Netbox)
        for index, row in results.items():
            self._update_interface(netbox, index, row)

    def _update_interface(self, netbox, ifindex, row):
        ifc = self.containers.factory(ifindex, shadows.Interface)
        ifc.netbox = netbox
        ifc.ifindex = ifindex
        if row['ifName']:
            ifc.ifname = row['ifName']
        ifc.ifoperstatus = row['ifOperStatus']

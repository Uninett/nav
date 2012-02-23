#
# Copyright (C) 2012 UNINETT AS
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
"""ipdevpoll plugin to collect LLDP neighbors

TODO: Identify known neighbors and update NAV database.

"""
from pprint import pformat

from twisted.internet import defer, threads

from nav.mibs.lldp_mib import LLDPMib
from nav.ipdevpoll import Plugin
from nav.ipdevpoll.neighbor import LLDPNeighbor

class LLDP(Plugin):
    "Collects devices' table of remote LLDP devices"
    remote = None
    neighbors = None

    @defer.inlineCallbacks
    def handle(self):
        mib = LLDPMib(self.agent)
        self.remote = yield mib.get_remote_table()
        if self.remote:
            self._logger.debug("LLDP neighbors:\n %s", pformat(self.remote))
        yield threads.deferToThread(self._process_remote)

    def _process_remote(self):
        "Tries to synchronously identify LLDP entries in NAV's database"
        neighbors = [LLDPNeighbor(lldp) for lldp in self.remote]
        identified = [n for n in neighbors if n.identified]
        for neigh in identified:
            self._logger.debug("identified neighbor %r from %r",
                               (neigh.netbox, neigh.interface), neigh.record)
        self.neighbors = neighbors

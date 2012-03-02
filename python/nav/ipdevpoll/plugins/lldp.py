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
"ipdevpoll plugin to collect LLDP neighbors"
from pprint import pformat

from twisted.internet import defer, threads

from nav.mibs.lldp_mib import LLDPMib
from nav.ipdevpoll import Plugin, shadows
from nav.ipdevpoll.neighbor import LLDPNeighbor

SOURCE = 'lldp'

class LLDP(Plugin):
    """Collects devices' table of remote LLDP devices.

    If the neighbor can be identified as something monitored by NAV, a
    topology adjacency candidate will be registered. Otherwise, the
    neighboring device will be noted as an unrecognized neighbor to this
    device.

    """
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
        shadows.AdjacencyCandidate.sentinel(self.containers, SOURCE)

        neighbors = [LLDPNeighbor(lldp) for lldp in self.remote]
        identified = [n for n in neighbors if n.identified]
        for neigh in identified:
            self._logger.debug("identified neighbor %r from %r",
                               (neigh.netbox, neigh.interface), neigh.record)
            self._store_candidate(neigh)
        self.neighbors = neighbors

    def _store_candidate(self, neighbor):
        ifindex = neighbor.record.ifindex
        ifc = self.containers.factory(ifindex, shadows.Interface)
        ifc.ifindex = ifindex

        key = (ifindex, neighbor.netbox.id, neighbor.interface.id, SOURCE)
        cand = self.containers.factory(key, shadows.AdjacencyCandidate)
        cand.netbox = self.netbox
        cand.interface = ifc
        cand.to_netbox = neighbor.netbox
        cand.to_interface = neighbor.interface
        cand.source = SOURCE

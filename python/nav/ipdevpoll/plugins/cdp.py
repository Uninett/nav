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
"ipdevpoll plugin to collect CDP (Cisco Discovery Protocol) information"
from twisted.internet import defer
from twisted.internet.threads import deferToThread

from nav.ipdevpoll import Plugin
from nav.mibs.cisco_cdp_mib import CiscoCDPMib
from nav.ipdevpoll.neighbor import CDPNeighbor

class CDP(Plugin):
    """Finds neighboring devices from a device's CDP cache.

    If the neighbor can be identified as something monitored by NAV, a
    topology adjacency candidate will be registered. Otherwise, the
    neighboring device will be noted as an unrecognized neighbor to this
    device.

    TODO: Actually fill some containers to store to db
    """
    cache = None
    neighbors = None

    @defer.inlineCallbacks
    def handle(self):
        cdp = CiscoCDPMib(self.agent)
        cache = yield cdp.get_cdp_neighbors()
        if cache:
            self._logger.debug("found CDP cache data: %r", cache)
            self.cache = cache
            yield deferToThread(self._process_cache)

    def _process_cache(self):
        "Tries to synchronously identify CDP cache entries in NAV's database"
        neighbors = [CDPNeighbor(cdp) for cdp in self.cache]
        identified = [n for n in neighbors if n.identified]
        for neigh in identified:
            self._logger.debug("identified neighbor %r from %r",
                               (neigh.netbox, neigh.interface), neigh.record)
        self.neighbors = neighbors

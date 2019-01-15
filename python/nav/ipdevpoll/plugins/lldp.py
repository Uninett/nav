#
# Copyright (C) 2012 Uninett AS
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
"ipdevpoll plugin to collect LLDP neighbors"
from pprint import pformat

from twisted.internet import defer

from nav.models import manage
from nav.mibs.lldp_mib import LLDPMib
from nav.ipdevpoll import Plugin, shadows
from nav.ipdevpoll.neighbor import LLDPNeighbor
from nav.ipdevpoll.db import run_in_thread
from nav.ipdevpoll.timestamps import TimestampChecker

INFO_VAR_NAME = 'lldp'
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

    @classmethod
    @defer.inlineCallbacks
    def can_handle(cls, netbox):
        daddy_says_ok = super(LLDP, cls).can_handle(netbox)
        has_ifcs = yield run_in_thread(cls._has_interfaces, netbox)
        defer.returnValue(has_ifcs and daddy_says_ok)

    @classmethod
    def _has_interfaces(cls, netbox):
        return manage.Interface.objects.filter(
            netbox__id=netbox.id).count() > 0

    @defer.inlineCallbacks
    def handle(self):
        mib = LLDPMib(self.agent)
        stampcheck = yield self._stampcheck(mib)
        need_to_collect = yield stampcheck.is_changed()
        if need_to_collect:
            self._logger.debug("collecting LLDP remote table")
            self.remote = yield mib.get_remote_table()
            if self.remote:
                self._logger.debug("LLDP neighbors:\n %s", pformat(self.remote))
            yield run_in_thread(self._process_remote)

            # Store sentinel to signal that LLDP neighbors have been processed
            shadows.AdjacencyCandidate.sentinel(self.containers, SOURCE)
        else:
            self._logger.debug("LLDP remote table seems unchanged")

        stampcheck.save()

    @defer.inlineCallbacks
    def _stampcheck(self, mib):
        stampcheck = TimestampChecker(self.agent, self.containers,
                                      INFO_VAR_NAME)
        yield stampcheck.load()
        yield stampcheck.collect([mib.get_remote_last_change()])

        defer.returnValue(stampcheck)

    def _process_remote(self):
        """Tries to synchronously identify LLDP entries in NAV's database"""
        neighbors = [LLDPNeighbor(lldp) for lldp in self.remote]

        self._process_identified(
            [n for n in neighbors if n.identified])
        self._process_unidentified(
            [n.record for n in neighbors if not n.identified])

        self.neighbors = neighbors

    def _process_identified(self, identified):
        for neigh in identified:
            self._logger.debug("identified neighbor %r from %r",
                               (neigh.netbox.sysname, neigh.interfaces), neigh.record)
            self._store_candidates(neigh)

    def _store_candidates(self, neighbor):
        if not neighbor.interfaces:
            return self._store_candidate(neighbor, None)
        for interface in neighbor.interfaces:
            self._store_candidate(neighbor, interface)

    def _store_candidate(self, neighbor, interface):
        ifindex = neighbor.record.ifindex
        ifc = self.containers.factory(ifindex, shadows.Interface)
        ifc.ifindex = ifindex

        key = (ifindex, self.netbox.id,
               neighbor.netbox.id,
               interface and interface.id or None,
               SOURCE,
               )
        cand = self.containers.factory(key, shadows.AdjacencyCandidate)
        cand.netbox = self.netbox
        cand.interface = ifc
        cand.to_netbox = neighbor.netbox
        cand.to_interface = interface
        cand.source = SOURCE

    def _process_unidentified(self, unidentified):
        for record in unidentified:
            self._store_unidentified(record)

    def _store_unidentified(self, record):
        ifc = self.containers.factory(record.ifindex, shadows.Interface)
        ifc.ifindex = record.ifindex

        key = (record.ifindex, record.chassis_id, SOURCE)
        neighbor = self.containers.factory(
            key, shadows.UnrecognizedNeighbor)
        neighbor.netbox = self.netbox
        neighbor.interface = ifc
        neighbor.remote_id = record.chassis_id
        neighbor.remote_name = record.sysname
        neighbor.source = SOURCE

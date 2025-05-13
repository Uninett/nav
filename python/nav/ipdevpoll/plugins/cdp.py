#
# Copyright (C) 2012 Uninett AS
# Copyright (C) 2022 Sikt
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
"ipdevpoll plugin to collect CDP (Cisco Discovery Protocol) information"

import string

from twisted.internet import defer

from nav.macaddress import MacAddress
from nav.models import manage
from nav.ipdevpoll import Plugin, shadows
from nav.mibs.cisco_cdp_mib import CiscoCDPMib
from nav.ipdevpoll.neighbor import Neighbor
from nav.ipdevpoll.db import run_in_thread
from nav.ipdevpoll.timestamps import TimestampChecker

INFO_VAR_NAME = "cdp"
INFO_KEY_NAME = "cdp"
INFO_VAR_NEIGHBORS_CACHE = "neighbors_cache"
SOURCE = "cdp"


class CDP(Plugin):
    """Finds neighboring devices from a device's CDP cache.

    If the neighbor can be identified as something monitored by NAV, a
    topology adjacency candidate will be registered. Otherwise, the
    neighboring device will be noted as an unrecognized neighbor to this
    device.

    """

    neighbors = None

    @classmethod
    @defer.inlineCallbacks
    def can_handle(cls, netbox):
        daddy_says_ok = super(CDP, cls).can_handle(netbox)
        has_ifcs = yield run_in_thread(cls._has_interfaces, netbox)
        return has_ifcs and daddy_says_ok

    @classmethod
    def _has_interfaces(cls, netbox):
        return manage.Interface.objects.filter(netbox__id=netbox.id).count() > 0

    @defer.inlineCallbacks
    def handle(self):
        cdp = CiscoCDPMib(self.agent)

        stampcheck = yield self._get_stampcheck(cdp)
        remote_table_has_changed = yield stampcheck.is_changed()
        need_to_collect = remote_table_has_changed

        if not remote_table_has_changed:
            cache = yield self._get_cached_neighbors()
            if cache is not None:
                self._logger.debug("Using cached CDP neighbors")
                self.neighbors = cache
            else:
                self._logger.debug(
                    "CDP cache table didn't change, but local cache was empty"
                )
                need_to_collect = True

        if need_to_collect:
            self._logger.debug("collecting CDP cache table")
            self.neighbors = yield cdp.get_cdp_neighbors()

        if self.neighbors:
            self._logger.debug("CDP neighbors:\n %r", self.neighbors)
            yield run_in_thread(self._process_neighbors)
            yield self._save_cached_neighbors(self.neighbors)
        else:
            self._logger.debug("No CDP neighbors to process")

        # Store sentinels to signal that CDP neighbors have been processed
        shadows.AdjacencyCandidate.sentinel(self.containers, SOURCE)
        shadows.UnrecognizedNeighbor.sentinel(self.containers, SOURCE)
        stampcheck.save()

    @defer.inlineCallbacks
    def _get_stampcheck(self, mib):
        stampcheck = TimestampChecker(self.agent, self.containers, INFO_VAR_NAME)
        yield stampcheck.load()
        yield stampcheck.collect([mib.get_neighbors_last_change()])

        return stampcheck

    @defer.inlineCallbacks
    def _get_cached_neighbors(self):
        """Retrieves a cached version of the remote neighbor table"""
        value = yield run_in_thread(
            manage.NetboxInfo.cache_get,
            self.netbox,
            INFO_KEY_NAME,
            INFO_VAR_NEIGHBORS_CACHE,
        )
        return value

    @defer.inlineCallbacks
    def _save_cached_neighbors(self, neighbors):
        """Saves a cached a copy of the remote neighbor table"""
        yield run_in_thread(
            manage.NetboxInfo.cache_set,
            self.netbox,
            INFO_KEY_NAME,
            INFO_VAR_NEIGHBORS_CACHE,
            neighbors,
        )

    def _process_neighbors(self):
        """
        Tries to synchronously identify CDP cache entries in NAV's database
        """
        neighbors = [CDPNeighbor(cdp, self.netbox.ip) for cdp in self.neighbors]

        self._process_identified([n for n in neighbors if n.identified])
        self._process_unidentified([n.record for n in neighbors if not n.identified])

    def _process_identified(self, identified):
        for neigh in identified:
            self._logger.debug(
                "identified neighbor %r from %r",
                (neigh.netbox, neigh.interfaces),
                neigh.record,
            )

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

        key = (
            ifindex,
            self.netbox.id,
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

        key = (record.ifindex, str(record.ip), SOURCE)
        neighbor = self.containers.factory(key, shadows.UnrecognizedNeighbor)
        neighbor.netbox = self.netbox
        neighbor.interface = ifc
        neighbor.remote_id = str(record.ip)
        neighbor.remote_name = record.deviceid
        neighbor.source = SOURCE


class CDPNeighbor(Neighbor):
    """Parses a CDP tuple from nav.mibs.cisco_cdp_mib to identify a neighbor"""

    def _identify_netbox(self):
        netbox = None
        if self.record.ip:
            netbox = self._netbox_from_ip(self.record.ip)

        if not netbox and self.record.deviceid:
            if looks_like_binary_garbage(self.record.deviceid):
                if len(self.record.deviceid) == 6:
                    try:
                        mac = MacAddress.from_octets(self.record.deviceid)
                    except TypeError:
                        pass
                    else:
                        netbox = self._netbox_from_mac(str(mac))
                else:
                    self._logger.debug(
                        "remote deviceid looks like garbage: %r", self.record.deviceid
                    )
            else:
                netbox = self._netbox_from_sysname(self.record.deviceid)
        return netbox

    def _identify_interfaces(self):
        return self._interfaces_from_name(self.record.deviceport)


def looks_like_binary_garbage(deviceid):
    """Determines whether the string looks like it contains binary garbage"""
    return any(c not in string.printable for c in deviceid)

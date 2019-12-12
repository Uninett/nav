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
"ipdevpoll plugin to collect CDP (Cisco Discovery Protocol) information"
import string

from django.utils import six
from twisted.internet import defer

from nav.macaddress import MacAddress
from nav.models import manage
from nav.ipdevpoll import Plugin, shadows
from nav.mibs.cisco_cdp_mib import CiscoCDPMib
from nav.ipdevpoll.neighbor import Neighbor
from nav.ipdevpoll.db import run_in_thread
from nav.ipdevpoll.timestamps import TimestampChecker

INFO_VAR_NAME = 'cdp'
SOURCE = 'cdp'


class CDP(Plugin):
    """Finds neighboring devices from a device's CDP cache.

    If the neighbor can be identified as something monitored by NAV, a
    topology adjacency candidate will be registered. Otherwise, the
    neighboring device will be noted as an unrecognized neighbor to this
    device.

    """
    cache = None
    neighbors = None

    @classmethod
    @defer.inlineCallbacks
    def can_handle(cls, netbox):
        daddy_says_ok = super(CDP, cls).can_handle(netbox)
        has_ifcs = yield run_in_thread(cls._has_interfaces, netbox)
        defer.returnValue(has_ifcs and daddy_says_ok)

    @classmethod
    def _has_interfaces(cls, netbox):
        return manage.Interface.objects.filter(
            netbox__id=netbox.id).count() > 0

    @defer.inlineCallbacks
    def handle(self):
        cdp = CiscoCDPMib(self.agent)
        stampcheck = yield self._stampcheck(cdp)
        need_to_collect = yield stampcheck.is_changed()
        if need_to_collect:
            self._logger.debug("collecting CDP cache table")
            cache = yield cdp.get_cdp_neighbors()
            if cache:
                self._logger.debug("found CDP cache data: %r", cache)
                self.cache = cache
                yield run_in_thread(self._process_cache)

            # Store sentinel to signal that CDP neighbors have been processed
            shadows.AdjacencyCandidate.sentinel(self.containers, SOURCE)

        else:
            self._logger.debug("CDP cache table seems unchanged")

        stampcheck.save()

    @defer.inlineCallbacks
    def _stampcheck(self, mib):
        stampcheck = TimestampChecker(self.agent, self.containers,
                                      INFO_VAR_NAME)
        yield stampcheck.load()
        yield stampcheck.collect([mib.get_neighbors_last_change()])

        defer.returnValue(stampcheck)

    def _process_cache(self):
        """
        Tries to synchronously identify CDP cache entries in NAV's database
        """
        neighbors = [CDPNeighbor(cdp, self.netbox.ip) for cdp in self.cache]

        self._process_identified(
            [n for n in neighbors if n.identified])
        self._process_unidentified(
            [n.record for n in neighbors if not n.identified])

        self.neighbors = neighbors

    def _process_identified(self, identified):
        for neigh in identified:
            self._logger.debug("identified neighbor %r from %r",
                               (neigh.netbox, neigh.interfaces), neigh.record)

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

        key = (record.ifindex, six.text_type(record.ip), SOURCE)
        neighbor = self.containers.factory(
            key, shadows.UnrecognizedNeighbor)
        neighbor.netbox = self.netbox
        neighbor.interface = ifc
        neighbor.remote_id = six.text_type(record.ip)
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

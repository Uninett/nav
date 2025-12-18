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
"""ipdevpoll plugin to collect LLDP neighbors"""

from pprint import pformat

from django.db.models import Q
from twisted.internet import defer

from nav.models import manage
from nav.mibs import lldp_mib
from nav.ipdevpoll import Plugin, shadows
from nav.ipdevpoll.neighbor import Neighbor
from nav.ipdevpoll.db import run_in_thread
from nav.ipdevpoll.timestamps import TimestampChecker

INFO_VAR_NAME = 'lldp'
SOURCE = 'lldp'
INFO_KEY_LLDP_INFO = "lldp"
INFO_VAR_CHASSIS_ID = "chassis_id"
INFO_VAR_CHASSIS_MAC = "chassis_mac"
INFO_VAR_REMOTES_CACHE = "remotes_cache"


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
        return has_ifcs and daddy_says_ok

    @classmethod
    def _has_interfaces(cls, netbox):
        return manage.Interface.objects.filter(netbox__id=netbox.id).count() > 0

    @defer.inlineCallbacks
    def handle(self):
        mib = lldp_mib.LLDPMib(self.agent)

        stampcheck = yield self._get_stampcheck(mib)
        remote_table_has_changed = yield stampcheck.is_changed()
        need_to_collect = remote_table_has_changed

        if not remote_table_has_changed:
            cache = yield self._get_cached_remote_table()
            if cache is not None:
                self._logger.debug("Using cached LLDP remote table")
                self.remote = cache
            else:
                self._logger.debug("Remote didn't change, but cache was empty")
                need_to_collect = True

        if need_to_collect:
            self._logger.debug("collecting LLDP remote table")
            self.remote = yield mib.get_remote_table()

        if self.remote:
            self._logger.debug("LLDP neighbors:\n %s", pformat(self.remote))
            yield run_in_thread(self._process_remote)
            yield self._get_chassis_id(mib)
            yield self._save_cached_remote_table(self.remote)
        else:
            self._logger.debug("No LLDP neighbors to process")

        # Store sentinels to signal that LLDP neighbors have been processed
        shadows.AdjacencyCandidate.sentinel(self.containers, SOURCE)
        shadows.UnrecognizedNeighbor.sentinel(self.containers, SOURCE)
        stampcheck.save()

    @defer.inlineCallbacks
    def _get_cached_remote_table(self):
        """Retrieves a cached version of the remote neighbor table"""
        value = yield run_in_thread(
            manage.NetboxInfo.cache_get,
            self.netbox,
            INFO_KEY_LLDP_INFO,
            INFO_VAR_REMOTES_CACHE,
        )
        return value

    @defer.inlineCallbacks
    def _save_cached_remote_table(self, remote_table):
        """Saves a cached copy of the remote neighbor table"""
        yield run_in_thread(
            manage.NetboxInfo.cache_set,
            self.netbox,
            INFO_KEY_LLDP_INFO,
            INFO_VAR_REMOTES_CACHE,
            remote_table,
        )

    @defer.inlineCallbacks
    def _get_chassis_id(self, mib):
        chassis_id_subtype = yield mib.get_next(
            "lldpLocChassisIdSubtype", translate_result=True
        )
        chassis_id = yield mib.get_next("lldpLocChassisId")
        if not chassis_id:
            return
        chassis_id = lldp_mib.IdSubtypes.get(chassis_id_subtype, chassis_id)
        info = self.containers.factory(
            (INFO_KEY_LLDP_INFO, INFO_VAR_CHASSIS_ID), shadows.NetboxInfo
        )
        info.value = str(chassis_id)
        info.netbox = self.netbox
        info.key = INFO_KEY_LLDP_INFO
        info.variable = INFO_VAR_CHASSIS_ID
        if isinstance(chassis_id, lldp_mib.MacAddress):
            info = self.containers.factory(
                (INFO_KEY_LLDP_INFO, INFO_VAR_CHASSIS_MAC), shadows.NetboxInfo
            )
            info.value = str(chassis_id)
            info.netbox = self.netbox
            info.key = INFO_KEY_LLDP_INFO
            info.variable = INFO_VAR_CHASSIS_MAC

    @defer.inlineCallbacks
    def _get_stampcheck(self, mib):
        """Retrieves the last change timestamp of the LLDP remote table, returning a
        TimestampChecker instance reflecting it.
        """
        stampcheck = TimestampChecker(self.agent, self.containers, INFO_VAR_NAME)
        yield stampcheck.load()
        yield stampcheck.collect([mib.get_remote_last_change()])

        return stampcheck

    def _process_remote(self):
        """Tries to synchronously identify LLDP entries in NAV's database"""
        neighbors = [LLDPNeighbor(lldp) for lldp in self.remote]

        self._process_identified([n for n in neighbors if n.identified])
        self._process_unidentified([n.record for n in neighbors if not n.identified])

        self.neighbors = neighbors

    def _process_identified(self, identified):
        for neigh in identified:
            self._logger.debug(
                "identified neighbor %r from %r",
                (neigh.netbox.sysname, neigh.interfaces),
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

        key = (record.ifindex, record.chassis_id, SOURCE)
        neighbor = self.containers.factory(key, shadows.UnrecognizedNeighbor)
        neighbor.netbox = self.netbox
        neighbor.interface = ifc
        neighbor.remote_id = record.chassis_id
        neighbor.remote_name = record.sysname
        neighbor.source = SOURCE


class LLDPNeighbor(Neighbor):
    "Parses an LLDP tuple from nav.mibs.lldp_mib to identify a neighbor"

    def _identify_netbox(self):
        chassid = self.record.chassis_id
        netbox = None
        if chassid:
            lookup = None
            if isinstance(chassid, lldp_mib.IdSubtypes.macAddress):
                lookup = self._netbox_from_mac
            elif isinstance(chassid, lldp_mib.IdSubtypes.networkAddress):
                lookup = self._netbox_from_ip
            elif isinstance(chassid, lldp_mib.IdSubtypes.local):
                lookup = self._netbox_from_local

            if lookup:
                netbox = lookup(str(chassid))

        if not netbox and self.record.sysname:
            netbox = self._netbox_from_sysname(self.record.sysname)

        return netbox

    def _netbox_from_local(self, chassid):
        # Some devices tend to put null bytes in local IDs, which make no sense and
        # will also not work in database queries. We cross our fingers and strip them
        # to avoid db issues:
        chassid = str(chassid).strip("\x00")
        if not chassid:
            return None  # stripped input was all garbage?
        netbox = self._netbox_query(
            Q(
                info_set__key=INFO_KEY_LLDP_INFO,
                info_set__variable=INFO_VAR_CHASSIS_ID,
                info_set__value=chassid,
            )
        )
        if netbox:
            self._logger.debug("Found netbox through local type lookup")
            return netbox
        else:
            return self._netbox_from_sysname(chassid)

    def _identify_interfaces(self):
        portid = self.record.port_id
        if self.netbox and portid:
            lookup = None
            if isinstance(
                portid,
                (lldp_mib.IdSubtypes.interfaceAlias, lldp_mib.IdSubtypes.interfaceName),
            ):
                lookup = self._interfaces_from_name
            elif isinstance(portid, (lldp_mib.IdSubtypes.local)):
                lookup = self._interfaces_from_local
            elif isinstance(portid, (lldp_mib.IdSubtypes.macAddress)):
                lookup = self._interfaces_from_mac
            elif isinstance(portid, (lldp_mib.IdSubtypes.networkAddress)):
                lookup = self._interfaces_from_ip

            if lookup:
                result = lookup(str(portid))
                if not result:
                    # IEEE 802.1AB-2005 9.5.5.2
                    portdesc = self.record.port_desc
                    if portdesc:
                        return self._interfaces_from_name(str(portdesc))
                else:
                    return result

    def _interfaces_from_local(self, portid):
        """Implements a heuristic seen on Juniper, where the port id is an
        ifIndex and the remote port description is the port's ifAlias value.
        If no match can be made this way, just revert to the regular "portid
        interpreted as name" lookup

        """
        portdesc = self.record.port_desc
        if portdesc and portid.isdigit():
            query = Q(ifindex=int(portid)) & Q(ifalias=portdesc)
            ifc = self._interface_query(query)
            if ifc:
                return ifc
        return self._interfaces_from_name(portid)

    def _interfaces_from_mac(self, mac):
        assert mac
        return self._interface_query(Q(ifphysaddress=mac))

    def _interfaces_from_ip(self, ip):
        ip = str(ip)
        assert ip
        if ip in self._invalid_neighbor_ips:
            return
        return self._interface_query(Q(gwport_prefixes__gw_ip=ip))

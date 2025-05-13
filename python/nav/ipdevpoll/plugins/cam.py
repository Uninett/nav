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
"ipdevpoll plugin to collect switch forwarding tables and STP blocking ports"

import re
from collections import defaultdict

from twisted.internet import defer

from nav.models import manage
from nav.util import splitby
from nav.mibs.bridge_mib import MultiBridgeMib
from nav.mibs.qbridge_mib import QBridgeMib
from nav.ipdevpoll import Plugin, db
from nav.ipdevpoll import shadows
from nav.ipdevpoll import utils
from nav.ipdevpoll.neighbor import get_netbox_macs


class Cam(Plugin):
    """Collects switches' forwarding tables and port STP states.

    For each port it finds forwarding data from, a decision is made:

    1. If the port reports any MAC address belonging to any NAV-monitored
       equipment, it is considered a topological port and one or more entries
       in the adjacency candidate table is made.

    2. Otherwise, the found forwarding entries are stored in NAV's cam table.

    """

    bridge = None
    fdb = None
    monitored = None
    dot1d_instances = None
    baseports = None
    linkports = None
    accessports = None
    blocking = None
    my_macs = None

    @classmethod
    @defer.inlineCallbacks
    def can_handle(cls, netbox):
        daddy_says_ok = super(Cam, cls).can_handle(netbox)
        has_ifcs = yield db.run_in_thread(cls._has_interfaces, netbox)
        return has_ifcs and daddy_says_ok

    @classmethod
    def _has_interfaces(cls, netbox):
        return manage.Interface.objects.filter(netbox__id=netbox.id).count() > 0

    @defer.inlineCallbacks
    def handle(self):
        """Gets forwarding tables from Q-BRIDGE-MIB. It that fails, reverts to
        BRIDGE-MIB, with optional community string indexing on Cisco.

        """
        fdb = yield self._get_dot1q_mac_port_mapping()
        self._log_fdb_stats("Q-BRIDGE-MIB", fdb)

        if not fdb:
            fdb = yield self._get_dot1d_mac_port_mapping()
            self._log_fdb_stats("BRIDGE-MIB", fdb)

        self.fdb = fdb

        self.monitored = yield db.run_in_thread(get_netbox_macs)
        self.my_macs = set(
            mac
            for mac, netboxid in self.monitored.items()
            if netboxid == self.netbox.id
        )
        self._classify_ports()
        self._store_cam_records()
        self._store_adjacency_candidates()

        self.blocking = yield self._get_dot1d_stp_blocking()

    @defer.inlineCallbacks
    def _get_dot1d_mac_port_mapping(self):
        bridge = yield self._get_bridge()
        fdb = yield bridge.get_forwarding_database()
        baseports = yield self._get_baseports()

        mapping = defaultdict(set)
        for mac, port in fdb.items():
            if port in baseports:
                ifindex = baseports[port]
                mapping[ifindex].add(mac)

        return dict(mapping)

    @defer.inlineCallbacks
    def _get_dot1q_mac_port_mapping(self):
        qbridge = QBridgeMib(self.agent)
        fdb = yield qbridge.get_forwarding_database()
        baseports = yield self._get_baseports()

        mapping = defaultdict(set)
        for mac, port in fdb:
            if port in baseports:
                ifindex = baseports[port]
                mapping[ifindex].add(mac)

        return dict(mapping)

    @defer.inlineCallbacks
    def _get_baseports(self):
        if not self.baseports:
            bridge = yield self._get_bridge()
            self.baseports = yield bridge.get_baseport_ifindex_map()
        return self.baseports

    @defer.inlineCallbacks
    def _get_bridge(self):
        if not self.bridge:
            instances = yield self._get_dot1d_instances()
            self.bridge = MultiBridgeMib(self.agent, instances)
        return self.bridge

    @defer.inlineCallbacks
    def _get_dot1d_instances(self):
        if not self.dot1d_instances:
            self.dot1d_instances = yield utils.get_dot1d_instances(self.agent)
        return self.dot1d_instances

    def _log_fdb_stats(self, prefix, fdb):
        mac_count = sum(len(v) for v in fdb.values())
        self._logger.debug(
            "%s: %d MAC addresses found on %d ports", prefix, mac_count, len(fdb)
        )

    def _classify_ports(self):
        def _is_linkport(portmacs):
            _port, macs = portmacs
            return any(
                mac in self.monitored and mac not in self.my_macs for mac in macs
            )

        linkports, accessports = splitby(_is_linkport, self.fdb.items())
        self.linkports = dict(linkports)
        self.accessports = dict(accessports)

        self._logger.debug("up/downlinks: %r", sorted(self.linkports.keys()))
        self._logger.debug("access ports: %r", sorted(self.accessports.keys()))

    def _store_cam_records(self):
        for port in self.accessports:
            macs = self.fdb.get(port, [])
            for mac in macs:
                self.containers.factory((port, mac), shadows.Cam, port, mac)
        shadows.Cam.manager.add_sentinel(self.containers)  # ensure cleanup!

    def _store_adjacency_candidates(self):
        shadows.AdjacencyCandidate.sentinel(self.containers, 'cam')
        for port in self.linkports:
            macs = self.fdb.get(port, None) or set()
            macs = macs.intersection(self.monitored).difference(self.my_macs)
            if macs:
                self._logger.debug(
                    "%r sees the following monitored mac addresses: %r", port, macs
                )
                candidates = [self.monitored[mac] for mac in macs]
                self._make_candidates(port, candidates)

    def _make_candidates(self, port, candidates):
        for netboxid in candidates:
            otherbox = self._factory_netbox(netboxid)
            ifc = self._factory_interface(port)

            candidate = self._factory_candidate(port, netboxid)
            candidate.interface = ifc
            candidate.to_netbox = otherbox
            candidate.source = 'cam'

    def _factory_netbox(self, netboxid):
        netbox = self.containers.factory(netboxid, shadows.Netbox)
        netbox.id = netboxid
        return netbox

    def _factory_interface(self, ifindex):
        ifc = self.containers.factory(ifindex, shadows.Interface)
        ifc.netbox = self.netbox
        ifc.ifindex = ifindex
        return ifc

    def _factory_candidate(self, port, candidate):
        candidate = self.containers.factory(
            (port, candidate, None, 'cam'), shadows.AdjacencyCandidate
        )
        candidate.netbox = self.netbox
        return candidate

    #
    # STP blocking related methods
    #
    # Currently, these are here just because we don't want to send multiple
    # duplicate queries to find multiple BRIDGE-MIB instances etc.  When SNMP
    # response caching is properly implemented, this should be extracted into
    # a separate plugin.
    #

    @defer.inlineCallbacks
    def _get_dot1d_stp_blocking(self):
        bridge = yield self._get_bridge()
        blocking = yield bridge.get_stp_blocking_ports()
        baseports = yield self._get_baseports()

        # Ensure processing of blocking states in DB, even if we found no
        # current blocking ports:
        self.containers.add(shadows.SwPortBlocked)

        translated = [
            (baseports[port], vlan) for port, vlan in blocking if port in baseports
        ]
        if translated:
            self._log_blocking_ports(translated)
            self._store_blocking_ports(translated)
        return translated

    def _log_blocking_ports(self, blocking):
        ifc_count = len(set(ifc for ifc, vlan in blocking))
        vlan_count = len(set(vlan for ifc, vlan in blocking))
        self._logger.debug(
            "found %d STP blocking ports on %d vlans: %r",
            ifc_count,
            vlan_count,
            blocking,
        )

    VLAN_PATTERN = re.compile('(vlan)?(?P<vlan>[0-9]+)', re.IGNORECASE)

    def _store_blocking_ports(self, blocking):
        for ifindex, vlan in blocking:
            if vlan:
                match = self.VLAN_PATTERN.match(vlan)
                vlan = int(match.group('vlan')) if match else None

            ifc = self.containers.factory(ifindex, shadows.Interface)
            ifc.ifindex = ifindex

            block = self.containers.factory((ifindex, vlan), shadows.SwPortBlocked)
            block.interface = ifc
            block.vlan = vlan

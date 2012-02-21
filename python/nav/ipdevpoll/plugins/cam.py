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
"ipdevpoll plugin to collect switch forwarding tables"
from collections import defaultdict
from datetime import timedelta

from twisted.internet import defer, threads

from nav.util import cachedfor
from nav.mibs.bridge_mib import MultiBridgeMib
from nav.mibs.qbridge_mib import QBridgeMib
from nav.mibs.entity_mib import EntityMib
from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll import utils

class Cam(Plugin):
    """Finds entries from switches' forwarding tables.

    For each port it finds data from, a decision is made:

    1. If the port reports any MAC address belonging to any NAV-monitored
       equipment, it is considered a topological port and one or more entries
       in the topological neighbor candidates table is made.

    2. Otherwise, the found forwarding entries are stored in NAV's cam table.

    TODO: Actually save data to containers.

    """
    bridge = None
    fdb = None
    monitored = None
    dot1d_instances = None
    baseports = None
    linkports = None
    accessports = None

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

        self.monitored = yield threads.deferToThread(get_netbox_macs)
        self._classify_ports()

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

        defer.returnValue(dict(mapping))

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

        defer.returnValue(dict(mapping))

    @defer.inlineCallbacks
    def _get_baseports(self):
        if not self.baseports:
            bridge = yield self._get_bridge()
            self.baseports = yield bridge.get_baseport_ifindex_map()
        defer.returnValue(self.baseports)

    @defer.inlineCallbacks
    def _get_bridge(self):
        if not self.bridge:
            instances = yield self._get_dot1d_instances()
            self.bridge = MultiBridgeMib(self.agent, instances)
        defer.returnValue(self.bridge)

    @defer.inlineCallbacks
    def _get_dot1d_instances(self):
        if not self.dot1d_instances:
            self.dot1d_instances = yield utils.get_dot1d_instances(self.agent)
        defer.returnValue(self.dot1d_instances)

    def _log_fdb_stats(self, prefix, fdb):
        mac_count = sum(len(v) for v in fdb.values())
        self._logger.debug("%s: %d MAC addresses found on %d ports",
                           prefix, mac_count, len(fdb))

    def _classify_ports(self):
        self.linkports = dict((port, macs) for port, macs in self.fdb.items()
                              if any(m in self.monitored for m in macs))

        self.accessports = dict((port, macs) for port, macs in self.fdb.items()
                                if port not in self.linkports)

        self._logger.debug("up/downlinks: %r", sorted(self.linkports.keys()))
        self._logger.debug("access ports: %r", sorted(self.accessports.keys()))


@cachedfor(timedelta(minutes=5))
def get_netbox_macs():
    "Returns a dict of (mac, netboxid) mappings of NAV-monitored devices"
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('SELECT mac, netboxid FROM netboxmac')
    netbox_macs = dict(cursor.fetchall())
    return netbox_macs

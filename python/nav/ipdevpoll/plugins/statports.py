#
# Copyright (C) 2013 UNINETT AS
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
"""Collects port traffic counters and pushes to Graphite"""
import time
from twisted.internet import defer
from nav.ipdevpoll import Plugin
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import metric_path_for_interface
from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib
from nav.mibs.ip_mib import IpMib


OCTET_COUNTERS = (
    "ifInOctets",
    "ifOutOctets",
)

HC_OCTET_COUNTERS = (
    "ifHCInOctets",
    "ifHCOutOctets",
)

OTHER_COUNTERS = (
    "ifInErrors",
    "ifOutErrors",
    "ifInUcastPkts",
    "ifOutUcastPkts",
    "ifInDiscards",
    "ifOutDiscards",
)

IF_IN_OCTETS_IPV6 = 'ifInOctetsIPv6'
IF_OUT_OCTETS_IPV6 = 'ifOutOctetsIPv6'

IP_COUNTERS = (
    IF_IN_OCTETS_IPV6,
    IF_OUT_OCTETS_IPV6,
)

USED_COUNTERS = OCTET_COUNTERS + HC_OCTET_COUNTERS + OTHER_COUNTERS
LOGGED_COUNTERS = USED_COUNTERS + IP_COUNTERS


class StatPorts(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        daddy_says_ok = super(StatPorts, cls).can_handle(netbox)
        return daddy_says_ok and netbox.category.id != 'EDGE'

    @defer.inlineCallbacks
    def handle(self):
        timestamp = time.time()
        stats = yield self._get_stats()
        tuples = list(self._make_metrics(stats, timestamp))
        if tuples:
            self._logger.debug("Counters collected")
            send_metrics(tuples)

    @defer.inlineCallbacks
    def _get_stats(self):
        ifmib = IfMib(self.agent)
        ipmib = IpMib(self.agent)
        stats = yield ifmib.retrieve_columns(
            ("ifName", "ifDescr") + USED_COUNTERS).addCallback(reduce_index)
        ipv6stats = yield ipmib.get_ipv6_octet_counters()
        if ipv6stats:
            self._logger.debug("found ipv6 octet counters for %d interfaces",
                               len(ipv6stats))
        for ifindex, (in_octets, out_octets) in ipv6stats.items():
            if ifindex in stats:
                stats[ifindex][IF_IN_OCTETS_IPV6] = in_octets
                stats[ifindex][IF_OUT_OCTETS_IPV6] = out_octets

        defer.returnValue(stats)

    def _make_metrics(self, stats, timestamp=None):
        timestamp = timestamp or time.time()
        hc_counters = False

        for row in stats.itervalues():
            hc_counters = use_hc_counters(row) or hc_counters
            for key in LOGGED_COUNTERS:
                if key not in row:
                    continue
                path = metric_path_for_interface(
                    self.netbox, row['ifName'] or row['ifDescr'], key)
                value = row[key]
                if value is not None:
                    yield (path, (timestamp, value))

        if stats:
            if hc_counters:
                self._logger.debug("High Capacity counters used")
            else:
                self._logger.debug("High Capacity counters NOT used")


def use_hc_counters(row):
    """
    Replaces octet counter values with high capacity counter values, if present
    """
    result = False
    for hc, nonhc in zip(HC_OCTET_COUNTERS, OCTET_COUNTERS):
        if row.get(hc, None) is not None:
            result = True
            row[nonhc] = row[hc]
        if hc in row:
            del row[hc]
    return result

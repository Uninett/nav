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
from pprint import pformat

from nav import graphite
from nav.graphite import metric_path_for_interface
from nav.ipdevpoll import Plugin
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
)

IP_COUNTERS = (
    'ipv6InOctets',
    'ipv6OutOctets',
)

USED_COUNTERS = OCTET_COUNTERS + OTHER_COUNTERS
LOGGED_COUNTERS = USED_COUNTERS + IP_COUNTERS


class StatPorts(Plugin):
    @defer.inlineCallbacks
    def handle(self):
        stats = yield self._get_stats()
        tuples = list(self._make_metrics(stats))
        self._logger.debug("collected: %s", pformat(tuples))
        if tuples:
            graphite.send_metrics(tuples)

    @defer.inlineCallbacks
    def _get_stats(self):
        ifmib = IfMib(self.agent)
        ipmib = IpMib(self.agent)
        stats = yield ifmib.retrieve_columns(
            ("ifName", "ifDescr") + USED_COUNTERS).addCallback(reduce_index)
        ipv6stats = yield ipmib.get_ipv6_octet_counters()
        for ifindex, (in_octets, out_octets) in ipv6stats.items():
            if ifindex in stats:
                stats[ifindex]['ipv6InOctets'] = in_octets
                stats[ifindex]['ipv6OutOctets'] = out_octets

        defer.returnValue(stats)

    def _make_metrics(self, stats):
        timestamp = time.time()

        for row in stats.itervalues():
            use_hc_counters(row)
            for key in LOGGED_COUNTERS:
                if key not in row:
                    continue
                path = metric_path_for_interface(
                    self.netbox, row['ifName'] or row['ifDescr'], key)
                value = row[key]
                if value is not None:
                    yield (path, (timestamp, value))


def use_hc_counters(row):
    """
    Replaces octet counter values with high capacity counter values, if present
    """
    for hc, nonhc in zip(HC_OCTET_COUNTERS, OCTET_COUNTERS):
        if row.get(hc, None) is not None:
            row[nonhc] = row[hc]


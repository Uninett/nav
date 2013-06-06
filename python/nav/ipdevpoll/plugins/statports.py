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
from nav.graphite import escape_metric_name
from nav.ipdevpoll import Plugin
from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib


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

USED_COUNTERS = OCTET_COUNTERS + OTHER_COUNTERS


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
        mib = IfMib(self.agent)
        stats = yield mib.retrieve_columns(("ifName", "ifDescr") +
                                           USED_COUNTERS)
        defer.returnValue(reduce_index(stats))

    def _make_metrics(self, stats):
        timestamp = time.time()
        sysname = escape_metric_name(self.netbox.sysname)

        for row in stats.itervalues():
            ifname = escape_metric_name(row['ifName'] or row['ifDescr'])
            use_hc_counters(row)
            for key in USED_COUNTERS:
                if key not in row:
                    continue
                path = "nav.devices.%s.ports.%s.%s" % (sysname, ifname, key)
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


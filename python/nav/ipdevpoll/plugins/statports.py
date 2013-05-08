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
from nav import graphite
from nav.ipdevpoll import Plugin
from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib
from pprint import pformat

COUNTERS = (
    "ifHCInOctets",
    "ifHCOutOctets",
    "ifInErrors",
    "ifOutErrors",
    "ifInUcastPkts",
    "ifOutUcastPkts",
)


class StatPorts(Plugin):
    @defer.inlineCallbacks
    def handle(self):
        stats = yield self._get_stats()
        tuples = list(self._make_metrics(stats))
        self._logger.debug("collected: %s", pformat(tuples))
        if tuples:
            graphite.send_metrics_to(tuples, '127.0.0.1')

    @defer.inlineCallbacks
    def _get_stats(self):
        mib = IfMib(self.agent)
        stats = yield mib.retrieve_columns(("ifName", "ifDescr") + COUNTERS)
        defer.returnValue(reduce_index(stats))

    def _make_metrics(self, stats):
        timestamp = time.time()
        sysname = escape_metric_name(self.netbox.sysname)

        for row in stats.itervalues():
            ifname = escape_metric_name(row['ifName'] or row['ifDescr'])
            for key in COUNTERS:
                if key not in row:
                    continue
                path = "nav.ports.%s.%s.%s" % (sysname, ifname, key)
                value = row[key]
                if value is not None:
                    yield (path, (timestamp, value))


def escape_metric_name(string):
    for char in "./ ":
        string = string.replace(char, "_")
    return string

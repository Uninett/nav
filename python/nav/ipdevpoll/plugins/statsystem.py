#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Collects system statistics and pushes to Graphite"""
import time

from twisted.internet import defer

from nav import graphite
from nav.graphite import escape_metric_name
from nav.ipdevpoll import Plugin

from nav.mibs.esswitch_mib import ESSwitchMib
from nav.mibs.cisco_c2900_mib import CiscoC2900Mib
from nav.mibs.cisco_stack_mib import CiscoStackMib
from nav.mibs.old_cisco_cpu_mib import OldCiscoCpuMib
from nav.mibs.cisco_process_mib import CiscoProcessMib

# TODO: Implement CPU stats from HP
# TODO: Implement CPU stats from Juniper?

SYSTEM_PREFIX = "nav.devices.{sysname}.system"


class StatSystem(Plugin):
    """Collects system statistics and pushes to Graphite"""
    BANDWIDTH_MIBS = [CiscoStackMib, CiscoC2900Mib, ESSwitchMib]
    CPU_MIBS = [CiscoProcessMib, OldCiscoCpuMib]

    @defer.inlineCallbacks
    def handle(self):
        bandwidth = yield self._collect_bandwidth()
        cpu = yield self._collect_cpu()
        metrics = bandwidth + cpu
        if metrics:
            graphite.send_metrics_to(metrics, '127.0.0.1')

    @defer.inlineCallbacks
    def _collect_bandwidth(self):
        for mibclass in self.BANDWIDTH_MIBS:
            mib = mibclass(self.agent)
            try:
                bandwidth = yield mib.get_bandwidth()
                bandwidth_peak = yield mib.get_bandwidth_peak()
                percent = False
            except AttributeError:
                bandwidth = yield mib.get_bandwidth_percent()
                bandwidth_peak = yield mib.get_bandwidth_percent_peak()
                percent = True

            if bandwidth or bandwidth_peak:
                self._logger.debug("Found bandwidth values from %s: %s, %s",
                                   mib.mib['moduleName'], bandwidth,
                                   bandwidth_peak)
                path_prefix = SYSTEM_PREFIX.format(
                    sysname=escape_metric_name(self.netbox.sysname))
                path_suffix = "_percent" if percent else ""
                timestamp = time.time()
                metrics = [
                    ("%s.bandwith%s" % (path_prefix, path_suffix),
                     (timestamp, bandwidth)),
                    ("%s.bandwith_peak%s" % (path_prefix, path_suffix),
                     (timestamp, bandwidth_peak)),
                ]
                defer.returnValue(metrics)
        defer.returnValue([])

    @defer.inlineCallbacks
    def _collect_cpu(self):
        for mibclass in self.CPU_MIBS:
            mib = mibclass(self.agent)
            avgbusy = yield mib.get_avgbusy()

            timestamp = time.time()
            if avgbusy:
                self._logger.debug("Found CPU values from %s: %s",
                                   mib.mib['moduleName'], avgbusy)
                metrics = []
                for cpuname, (avgbusy1, avgbusy5) in avgbusy.items():
                    path_prefix = SYSTEM_PREFIX.format(
                        sysname=escape_metric_name(self.netbox.sysname))
                    cpu_path = "%s.%s" % (path_prefix,
                                          escape_metric_name(cpuname))
                    metrics.extend((
                        ("%s.%s" % (cpu_path, 'avgbusy5'),
                         (timestamp, avgbusy5)),
                        ("%s.%s" % (cpu_path, 'avgbusy1'),
                         (timestamp, avgbusy1)),
                    ))
                defer.returnValue(metrics)
        defer.returnValue([])

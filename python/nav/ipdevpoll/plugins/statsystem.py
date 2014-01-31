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
from twisted.internet.error import TimeoutError

from nav.ipdevpoll import Plugin
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import (
    metric_path_for_bandwith,
    metric_path_for_bandwith_peak,
    metric_path_for_cpu_load,
    metric_path_for_cpu_utilization,
    metric_path_for_sysuptime,
    metric_prefix_for_memory
)
from nav.mibs.cisco_memory_pool_mib import CiscoMemoryPoolMib

from nav.mibs.esswitch_mib import ESSwitchMib
from nav.mibs.cisco_c2900_mib import CiscoC2900Mib
from nav.mibs.cisco_stack_mib import CiscoStackMib
from nav.mibs.netswitch_mib import NetswitchMib
from nav.mibs.old_cisco_cpu_mib import OldCiscoCpuMib
from nav.mibs.cisco_process_mib import CiscoProcessMib
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.mibs.statistics_mib import StatisticsMib
from nav.mibs.juniper_mib import JuniperMib

VENDORID_CISCO = 9
VENDORID_HP = 11
VENDORID_JUNIPER = 2636

BANDWIDTH_MIBS = {
    VENDORID_CISCO: [CiscoStackMib, CiscoC2900Mib, ESSwitchMib],
}

CPU_MIBS = {
    VENDORID_CISCO: [CiscoProcessMib, OldCiscoCpuMib],
    VENDORID_HP: [StatisticsMib],
    VENDORID_JUNIPER: [JuniperMib],
}

MEMORY_MIBS = {
    VENDORID_CISCO: [CiscoMemoryPoolMib],
    VENDORID_HP: [NetswitchMib],
}


class StatSystem(Plugin):
    """Collects system statistics and pushes to Graphite"""
    @defer.inlineCallbacks
    def handle(self):
        bandwidth = yield self._collect_bandwidth()
        cpu = yield self._collect_cpu()
        sysuptime = yield self._collect_sysuptime()
        memory = yield self._collect_memory()

        metrics = bandwidth + cpu + sysuptime + memory
        if metrics:
            send_metrics(metrics)

    @defer.inlineCallbacks
    def _collect_bandwidth(self):
        for mib in self._mibs_for_me(BANDWIDTH_MIBS):
            try:
                metrics = yield self._collect_bandwidth_from_mib(mib)
            except (TimeoutError, defer.TimeoutError):
                self._logger.debug("collect_bandwidth: ignoring timeout in %s",
                                   mib.mib['moduleName'])
            else:
                if metrics:
                    defer.returnValue(metrics)
        defer.returnValue([])

    @defer.inlineCallbacks
    def _collect_bandwidth_from_mib(self, mib):
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
            timestamp = time.time()
            metrics = [
                (metric_path_for_bandwith(self.netbox, percent),
                 (timestamp, bandwidth)),
                (metric_path_for_bandwith_peak(self.netbox, percent),
                 (timestamp, bandwidth_peak)),
            ]
            defer.returnValue(metrics)

    @defer.inlineCallbacks
    def _collect_cpu(self):
        for mib in self._mibs_for_me(CPU_MIBS):
            try:
                load = yield self._get_cpu_loadavg(mib)
                utilization = yield self._get_cpu_utilization(mib)
            except (TimeoutError, defer.TimeoutError):
                self._logger.debug("collect_cpu: ignoring timeout in %s",
                                   mib.mib['moduleName'])
            else:
                defer.returnValue(load + utilization)
        defer.returnValue([])

    @defer.inlineCallbacks
    def _get_cpu_loadavg(self, mib):
        load = yield mib.get_cpu_loadavg()
        timestamp = time.time()
        metrics = []

        if load:
            self._logger.debug("Found CPU loadavg from %s: %s",
                               mib.mib['moduleName'], load)
            for cpuname, loadlist in load.items():
                for interval, value in loadlist:
                    path = metric_path_for_cpu_load(self.netbox, cpuname,
                                                    interval)
                    metrics.append((path, (timestamp, value)))
        defer.returnValue(metrics)

    @defer.inlineCallbacks
    def _get_cpu_utilization(self, mib):
        utilization = yield mib.get_cpu_utilization()
        timestamp = time.time()
        metrics = []

        if utilization:
            self._logger.debug("Found CPU utilization from %s: %s",
                               mib.mib['moduleName'], utilization)
            for cpuname, value in utilization.items():
                path = metric_path_for_cpu_utilization(self.netbox, cpuname)
                metrics.append((path, (timestamp, value)))
        defer.returnValue(metrics)

    def _mibs_for_me(self, mib_class_dict):
        vendor = (self.netbox.type.get_enterprise_id()
                  if self.netbox.type else None)
        mib_classes = (mib_class_dict.get(vendor, None) or
                       mib_class_dict.get(None, []))
        for mib_class in mib_classes:
            yield mib_class(self.agent)

    @defer.inlineCallbacks
    def _collect_sysuptime(self):
        mib = Snmpv2Mib(self.agent)
        uptime = yield mib.get_sysUpTime()
        timestamp = time.time()

        if uptime:
            path = metric_path_for_sysuptime(self.netbox)
            defer.returnValue([(path, (timestamp, uptime))])
        else:
            defer.returnValue([])

    @defer.inlineCallbacks
    def _collect_memory(self):
        memory = dict()
        for mib in self._mibs_for_me(MEMORY_MIBS):
            try:
                mem = yield mib.get_memory_usage()
            except (TimeoutError, defer.TimeoutError):
                self._logger.debug("collect_memory: ignoring timeout in %s",
                                   mib.mib['moduleName'])
            else:
                if mem:
                    self._logger.debug("Found memory values from %s: %r",
                                       mib.mib['moduleName'], mem)
                    memory.update(mem)

        timestamp = time.time()
        result = []
        for name, (used, free) in memory.items():
            prefix = metric_prefix_for_memory(self.netbox, name)
            result.extend([
                (prefix + '.used', (timestamp, used)),
                (prefix + '.free', (timestamp, free)),
            ])
        defer.returnValue(result)

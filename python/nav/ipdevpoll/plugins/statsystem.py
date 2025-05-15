#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
from nav.ipdevpoll import db
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import (
    metric_path_for_bandwith,
    metric_path_for_bandwith_peak,
    metric_path_for_cpu_load,
    metric_path_for_cpu_utilization,
    metric_path_for_sysuptime,
    metric_path_for_power,
    metric_prefix_for_memory,
)
from nav.mibs.cisco_memory_pool_mib import CiscoMemoryPoolMib
from nav.mibs.cisco_enhanced_memory_pool_mib import CiscoEnhancedMemoryPoolMib

from nav.mibs.esswitch_mib import ESSwitchMib
from nav.mibs.cisco_c2900_mib import CiscoC2900Mib
from nav.mibs.cisco_stack_mib import CiscoStackMib
from nav.mibs.netswitch_mib import NetswitchMib
from nav.mibs.old_cisco_cpu_mib import OldCiscoCpuMib
from nav.mibs.cisco_process_mib import CiscoProcessMib
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.mibs.statistics_mib import StatisticsMib
from nav.mibs.juniper_mib import JuniperMib
from nav.mibs.power_ethernet_mib import PowerEthernetMib
from nav.enterprise.ids import (
    VENDOR_ID_CISCOSYSTEMS,
    VENDOR_ID_HEWLETT_PACKARD,
    VENDOR_ID_JUNIPER_NETWORKS_INC,
)


BANDWIDTH_MIBS = {
    VENDOR_ID_CISCOSYSTEMS: [CiscoStackMib, CiscoC2900Mib, ESSwitchMib],
}

CPU_MIBS = {
    VENDOR_ID_CISCOSYSTEMS: [CiscoProcessMib, OldCiscoCpuMib],
    VENDOR_ID_HEWLETT_PACKARD: [StatisticsMib],
    VENDOR_ID_JUNIPER_NETWORKS_INC: [JuniperMib],
}

MEMORY_MIBS = {
    VENDOR_ID_CISCOSYSTEMS: [CiscoMemoryPoolMib, CiscoEnhancedMemoryPoolMib],
    VENDOR_ID_HEWLETT_PACKARD: [NetswitchMib],
    VENDOR_ID_JUNIPER_NETWORKS_INC: [JuniperMib],
}


class StatSystem(Plugin):
    """Collects system statistics and pushes to Graphite"""

    @defer.inlineCallbacks
    def handle(self):
        if self.netbox.master:
            return None
        netboxes = yield db.run_in_thread(self._get_netbox_list)
        bandwidth = yield self._collect_bandwidth(netboxes)
        cpu = yield self._collect_cpu(netboxes)
        sysuptime = yield self._collect_sysuptime(netboxes)
        memory = yield self._collect_memory(netboxes)
        power = yield self._collect_power(netboxes)

        metrics = bandwidth + cpu + sysuptime + memory + power
        if metrics:
            send_metrics(metrics)

    @defer.inlineCallbacks
    def _collect_bandwidth(self, netboxes):
        for mib in self._mibs_for_me(BANDWIDTH_MIBS):
            try:
                metrics = yield self._collect_bandwidth_from_mib(mib, netboxes)
            except (TimeoutError, defer.TimeoutError):
                self._logger.debug(
                    "collect_bandwidth: ignoring timeout in %s", mib.mib['moduleName']
                )
            else:
                if metrics:
                    return metrics
        return []

    @defer.inlineCallbacks
    def _collect_bandwidth_from_mib(self, mib, netboxes):
        try:
            bandwidth = yield mib.get_bandwidth()
            bandwidth_peak = yield mib.get_bandwidth_peak()
            percent = False
        except AttributeError:
            bandwidth = yield mib.get_bandwidth_percent()
            bandwidth_peak = yield mib.get_bandwidth_percent_peak()
            percent = True

        if bandwidth or bandwidth_peak:
            self._logger.debug(
                "Found bandwidth values from %s: %s, %s",
                mib.mib['moduleName'],
                bandwidth,
                bandwidth_peak,
            )
            timestamp = time.time()
            metrics = []
            for netbox in netboxes:
                metrics += [
                    (metric_path_for_bandwith(netbox, percent), (timestamp, bandwidth)),
                    (
                        metric_path_for_bandwith_peak(netbox, percent),
                        (timestamp, bandwidth_peak),
                    ),
                ]
            return metrics

    @defer.inlineCallbacks
    def _collect_cpu(self, netboxes):
        for mib in self._mibs_for_me(CPU_MIBS):
            try:
                load = yield self._get_cpu_loadavg(mib, netboxes)
                utilization = yield self._get_cpu_utilization(mib, netboxes)
            except (TimeoutError, defer.TimeoutError):
                self._logger.debug(
                    "collect_cpu: ignoring timeout in %s", mib.mib['moduleName']
                )
            else:
                return load + utilization
        return []

    @defer.inlineCallbacks
    def _get_cpu_loadavg(self, mib, netboxes):
        load = yield mib.get_cpu_loadavg()
        timestamp = time.time()
        metrics = []

        if load:
            self._logger.debug(
                "Found CPU loadavg from %s: %s", mib.mib['moduleName'], load
            )
            for cpuname, loadlist in load.items():
                for interval, value in loadlist:
                    for netbox in netboxes:
                        path = metric_path_for_cpu_load(netbox, cpuname, interval)
                        metrics.append((path, (timestamp, value)))
        return metrics

    @defer.inlineCallbacks
    def _get_cpu_utilization(self, mib, netboxes):
        utilization = yield mib.get_cpu_utilization()
        timestamp = time.time()
        metrics = []

        if utilization:
            self._logger.debug(
                "Found CPU utilization from %s: %s", mib.mib['moduleName'], utilization
            )
            for cpuname, value in utilization.items():
                for netbox in netboxes:
                    path = metric_path_for_cpu_utilization(netbox, cpuname)
                    metrics.append((path, (timestamp, value)))
        return metrics

    def _mibs_for_me(self, mib_class_dict):
        vendor = self.netbox.type.get_enterprise_id() if self.netbox.type else None
        mib_classes = mib_class_dict.get(vendor, None) or mib_class_dict.get(None, [])
        self._logger.debug("mibs for me (vendor=%s): %r", vendor, mib_classes)
        for mib_class in mib_classes:
            yield mib_class(self.agent)

    @defer.inlineCallbacks
    def _collect_sysuptime(self, netboxes):
        mib = Snmpv2Mib(self.agent)
        uptime = yield mib.get_sysUpTime()
        timestamp = time.time()

        if uptime:
            metrics = []
            for netbox in netboxes:
                path = metric_path_for_sysuptime(netbox)
                metrics.append((path, (timestamp, uptime)))
            return metrics
        else:
            return []

    @defer.inlineCallbacks
    def _collect_power(self, netboxes):
        mib = PowerEthernetMib(self.agent)
        power = yield mib.get_groups_table()
        self._logger.debug("Got poe data %s", power)
        power = {
            key: val['pethMainPseConsumptionPower']
            for key, val in power.items()
            if val['pethMainPseOperStatus'] == 1
        }
        timestamp = time.time()

        if power:
            metrics = []
            for netbox in netboxes:
                for index, value in power.items():
                    path = metric_path_for_power(netbox, index)
                    metrics.append((path, (timestamp, value)))
            return metrics
        else:
            return []

    @defer.inlineCallbacks
    def _collect_memory(self, netboxes):
        memory = dict()
        for mib in self._mibs_for_me(MEMORY_MIBS):
            try:
                mem = yield mib.get_memory_usage()
            except (TimeoutError, defer.TimeoutError):
                self._logger.debug(
                    "collect_memory: ignoring timeout in %s", mib.mib['moduleName']
                )
            else:
                if mem:
                    self._logger.debug(
                        "Found memory values from %s: %r", mib.mib['moduleName'], mem
                    )
                    memory.update(mem)

        timestamp = time.time()
        result = []
        for name, (used, free) in memory.items():
            for netbox in netboxes:
                prefix = metric_prefix_for_memory(netbox, name)
                result.extend(
                    [
                        (prefix + '.used', (timestamp, used)),
                        (prefix + '.free', (timestamp, free)),
                    ]
                )
        return result

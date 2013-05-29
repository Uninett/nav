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
from nav.mibs.statistics_mib import StatisticsMib

# TODO: Implement CPU stats from Juniper?

VENDORID_CISCO = 9
VENDORID_HP = 11


class StatSystem(Plugin):
    """Collects system statistics and pushes to Graphite"""
    BANDWIDTH_MIBS = {
        VENDORID_CISCO: [CiscoStackMib, CiscoC2900Mib, ESSwitchMib],
    }

    CPU_MIBS = {
        VENDORID_CISCO: [CiscoProcessMib, OldCiscoCpuMib],
        VENDORID_HP: [StatisticsMib],
    }

    @defer.inlineCallbacks
    def handle(self):
        bandwidth = yield self._collect_bandwidth()
        cpu = yield self._collect_cpu()

        metrics = bandwidth + cpu
        if metrics:
            graphite.send_metrics_to(metrics, '127.0.0.1')

    @defer.inlineCallbacks
    def _collect_bandwidth(self):
        for mib in self._mibs_for_me(self.BANDWIDTH_MIBS):
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
        defer.returnValue([])

    @defer.inlineCallbacks
    def _collect_cpu(self):
        for mib in self._mibs_for_me(self.CPU_MIBS):
            metrics = yield self._get_avgbusy(mib)
            if not metrics:
                metrics = yield self._get_cpu_load(mib)
            defer.returnValue(metrics or [])
        defer.returnValue([])

    @defer.inlineCallbacks
    def _get_avgbusy(self, mib):
        if not hasattr(mib, 'get_avgbusy'):
            defer.returnValue([])

        avgbusy = yield mib.get_avgbusy()
        timestamp = time.time()

        if avgbusy:
            self._logger.debug("Found CPU values from %s: %s",
                               mib.mib['moduleName'], avgbusy)
            metrics = []
            for cpuname, (avgbusy1, avgbusy5) in avgbusy.items():
                metrics.extend((
                    (metric_path_for_cpu_avgbusy(self.netbox, cpuname, 5),
                     (timestamp, avgbusy5)),
                    (metric_path_for_cpu_avgbusy(self.netbox, cpuname, 1),
                     (timestamp, avgbusy1)),
                ))
            defer.returnValue(metrics)
        defer.returnValue([])

    @defer.inlineCallbacks
    def _get_cpu_load(self, mib):
        if not hasattr(mib, 'get_cpu_utilization'):
            defer.returnValue([])

        utilization = yield mib.get_cpu_utilization()
        timestamp = time.time()

        if utilization:
            self._logger.debug("Found CPU load from %s: %s",
                               mib.mib['moduleName'], utilization)
            defer.returnValue([
                (metric_path_for_cpu_load(self.netbox, 'cpu'),
                 (timestamp, utilization))
            ])

    def _mibs_for_me(self, mib_class_dict):
        vendor = (self.netbox.type.get_enterprise_id()
                  if self.netbox.type else None)
        mib_classes = (mib_class_dict.get(vendor, None) or
                       mib_class_dict.get(None, []))
        for mib_class in mib_classes:
            yield mib_class(self.agent)

#
# metric path templates
#


def metric_path_for_bandwith(sysname, is_percent):
    tmpl = "{prefix}.bandwidth{percent}"
    return tmpl.format(prefix=metric_prefix_for_system(sysname),
                       percent="_percent" if is_percent else "")


def metric_path_for_bandwith_peak(sysname, is_percent):
    tmpl = "{prefix}.bandwidth_peak{percent}"
    return tmpl.format(prefix=metric_prefix_for_system(sysname),
                       percent="_percent" if is_percent else "")


def metric_path_for_cpu_avgbusy(sysname, cpu_name, interval):
    tmpl = "{prefix}.{cpu_name}.avgbusy{interval}"
    return tmpl.format(prefix=metric_prefix_for_system(sysname),
                       cpu_name=escape_metric_name(cpu_name),
                       interval=escape_metric_name(str(interval)))


def metric_path_for_cpu_load(sysname, cpu_name):
    tmpl = "{prefix}.{cpu_name}.cpuload"
    return tmpl.format(prefix=metric_prefix_for_system(sysname),
                       cpu_name=escape_metric_name(cpu_name))


def metric_prefix_for_system(sysname):
    tmpl = "nav.devices.{sysname}.system"
    if hasattr(sysname, 'sysname'):
        sysname = sysname.sysname
    return tmpl.format(sysname=escape_metric_name(sysname))

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


class StatSystem(Plugin):
    """Collects system statistics and pushes to Graphite"""


    @defer.inlineCallbacks
    def handle(self):
        bandwidth = yield self._collect_bandwidth()
        graphite.send_metrics_to(bandwidth, '127.0.0.1')

    @defer.inlineCallbacks
    def _collect_bandwidth(self):
        for mibclass in self.MIBS:
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
                path_prefix = ("nav.devices.%s.system" %
                               escape_metric_name(self.netbox.sysname))
                path_suffix = "_percent" if percent else ""
                timestamp = time.time()
                metrics = [
                    ("%s.bandwith%s" % (path_prefix, path_suffix),
                     (timestamp, bandwidth)),
                    ("%s.bandwith_peak%s" % (path_prefix, path_suffix),
                     (timestamp, bandwidth_peak)),
                ]
                defer.returnValue(metrics)

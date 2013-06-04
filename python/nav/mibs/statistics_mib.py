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
"""HP STATISTICS-MIB"""
from twisted.internet import defer
from nav.mibs import mibretriever


class StatisticsMib(mibretriever.MibRetriever):
    """HP STATISTICS-MIB"""
    from nav.smidumps.statistics_mib import MIB as mib

    @defer.inlineCallbacks
    def get_cpu_utilization(self):
        """Returns the current switch CPU utilization in percent"""
        util = yield self.get_next('hpSwitchCpuStat')
        if util is not None:
            defer.returnValue(dict(cpu=util))

    def get_cpu_loadavg(self):
        return defer.succeed(None)

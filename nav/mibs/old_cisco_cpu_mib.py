#
# Copyright (C) 2013 Uninett AS
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
from twisted.internet import defer
from nav.mibs import mibretriever


class OldCiscoCpuMib(mibretriever.MibRetriever):
    from nav.smidumps.old_cisco_cpu_mib import MIB as mib

    @defer.inlineCallbacks
    def get_cpu_loadavg(self):
        avgbusy5 = yield self.get_next('avgBusy5')
        avgbusy1 = yield self.get_next('avgBusy1')
        if avgbusy5 or avgbusy1:
            result = dict(cpu=[(5, avgbusy5), (1, avgbusy1)])
            defer.returnValue(result)

    def get_cpu_utilization(self):
        return defer.succeed(None)

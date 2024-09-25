#
# Copyright (C) 2013 Uninett AS
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
from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs import mibretriever


class OldCiscoCpuMib(mibretriever.MibRetriever):
    mib = get_mib('OLD-CISCO-CPU-MIB')

    @defer.inlineCallbacks
    def get_cpu_loadavg(self):
        avgbusy5 = yield self.get_next('avgBusy5')
        avgbusy1 = yield self.get_next('avgBusy1')
        if avgbusy5 or avgbusy1:
            result = dict(cpu=[(5, avgbusy5), (1, avgbusy1)])
            return result

    def get_cpu_utilization(self):
        return defer.succeed(None)

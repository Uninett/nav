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
from nav.mibs import mibretriever


class CiscoStackMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_stack_mib import MIB as mib

    def get_bandwidth_percent(self):
        return self.get_next('sysTraffic')

    def get_bandwidth_percent_peak(self):
        return self.get_next('sysTrafficPeak')

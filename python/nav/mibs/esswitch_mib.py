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
"""STANDALONE-ETHERNET-SWITCH-MIB to get data from Cisco 1900 (originally by
Grand Junction Networks)

"""

from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs import mibretriever


class ESSwitchMib(mibretriever.MibRetriever):
    mib = get_mib('STAND-ALONE-ETHERNET-SWITCH-MIB')

    BANDWIDTH_USAGE_CURRENT = 'bandwidthUsageCurrent'
    BANDWIDTH_USAGE_CURRENT_PEAK_ENTRY = 'bandwidthUsageCurrentPeakEntry'
    BANDWIDTH_USAGE_CURRENT_PEAK = 'bandwidthUsagePeak'

    def get_bandwidth(self):
        """Retrieves the current bandwidth usage in Mbit/s"""
        return self.get_next(self.BANDWIDTH_USAGE_CURRENT)

    @defer.inlineCallbacks
    def get_bandwidth_peak(self):
        """Retrieves the peak bandwidth usage (in Mbit/s) within the
        device-configured measuering interval.

        """
        peak_index = yield self.get_next(self.BANDWIDTH_USAGE_CURRENT_PEAK_ENTRY)

        if peak_index:
            peak_oid = str(
                self.nodes[self.BANDWIDTH_USAGE_CURRENT_PEAK].oid + (peak_index,)
            )
            rsp = yield self.agent_proxy.get([peak_oid])
            return rsp.get(peak_oid, None)

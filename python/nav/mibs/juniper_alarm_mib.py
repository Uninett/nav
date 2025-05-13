#
# Copyright (C) 2023 Sikt
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
"""JUNIPER-ALARM-MIB MibRetriever"""

from twisted.internet import defer

from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever


class JuniperAlarmMib(MibRetriever):
    """JUNIPER-ALARM-MIB MibRetriever"""

    mib = get_mib("JUNIPER-ALARM-MIB")

    def get_yellow_alarm_count(self):
        """Tries to get a yellow alarm count from a Juniper device"""
        return self._get_alarm_count("jnxYellowAlarmCount")

    def get_red_alarm_count(self):
        """Tries to get a red alarm count from a Juniper device"""
        return self._get_alarm_count("jnxRedAlarmCount")

    @defer.inlineCallbacks
    def _get_alarm_count(self, oid):
        count = yield self.get_next(oid)
        try:
            count = int(count) or 0
        except (ValueError, TypeError):
            count = 0
        return count

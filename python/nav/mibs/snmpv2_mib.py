#
# Copyright (C) 2009-2012, 2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Implements a MibRetriever for the SNMPV2-MIB"""

import time

from twisted.internet import defer

from nav.Snmp import safestring
from nav.oids import OID
from nav.smidumps import get_mib
from . import mibretriever


class Snmpv2Mib(mibretriever.MibRetriever):
    """A MibRetriever for SNMPv2-MIB"""

    mib = get_mib('SNMPv2-MIB')

    @defer.inlineCallbacks
    def _get_sysvariable(self, var):
        """Retrieves a system variable of the first agent instance.

        Will first try get-next on {var}, then fall back to getting {var}.0 on
        failure.  This is a workaround for a faulty SNMP agent implementation
        observed in Weathergoose devices, where e.g. a GET-NEXT on sysObjectID
        would consistently return sysUpTime.0 instead.

        """
        oid = self.nodes[var].oid
        result = yield self.get_next(var)
        if result:
            return result
        else:
            oid = oid + OID('0')
            result = yield self.agent_proxy.get([str(oid)])
            for key, value in result.items():
                if oid == OID(key):
                    return value

    def get_sysObjectID(self):
        """Retrieves the sysObjectID of the first agent instance."""
        return self._get_sysvariable('sysObjectID')

    def get_sysDescr(self):
        """Retrieves the sysDescr of the first agent instance."""
        dfr = self._get_sysvariable('sysDescr')
        dfr.addCallback(safestring)
        return dfr

    def get_sysUpTime(self):
        """Retrieves the sysUpTime of the first agent instance."""
        return self._get_sysvariable('sysUpTime')

    @defer.inlineCallbacks
    def get_timestamp_and_uptime(self):
        """Retrieves the agent's current sysUpTime and gets the current system
        time.

        :returns: A tuple of (timestamp, collected_sysuptime)

        """
        sysuptime = yield self._get_sysvariable('sysUpTime')
        timestamp = time.mktime(time.localtime())
        return (timestamp, sysuptime)

    @staticmethod
    def get_uptime_deviation(first_uptime, second_uptime):
        """Calculates the deviation between two collected sysUpTime values and
        the expected delta of the two, based on the collection timestamp delta
        between the two.

        The calculation will take into account the fact that sysUpTime is a
        32-bit unsigned value measuring centiseconds, and will wrap around
        every ~497.10 days.

        :argument first_uptime: A (timestamp, sysUpTime) tuple. The timestamp
                                should be the wall clock of the NAV server
                                when the sysUpTime value was collected.

        :argument second_uptime: A (timestamp, sysUpTime) tuple. The
                                 timestamp should be the wall clock of the NAV
                                 server when the sysUpTime value was
                                 collected.

        :returns: The deviation, in seconds, between the collected uptime
        delta and the expected uptime delta.

        """
        tstamp1, uptime1 = first_uptime
        tstamp2, uptime2 = second_uptime

        if any(x is None for x in (tstamp1, tstamp2, uptime1, uptime2)):
            return

        expected_delta = (tstamp2 - tstamp1) * 100.0
        expected_uptime2 = (uptime1 + expected_delta) % 2**32
        deviation = (uptime2 - expected_uptime2) / 100.0
        return deviation

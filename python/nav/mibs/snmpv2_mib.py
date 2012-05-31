#
# Copyright (C) 2009-2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"Implements a MibRetriever for the SNMPV2-MIB"

import time

from twisted.internet import defer

from nav.oids import OID
import mibretriever

class Snmpv2Mib(mibretriever.MibRetriever):
    from nav.smidumps.snmpv2_mib import MIB as mib

    def _get_sysvariable(self, var):
        """Retrieves a system variable of the first agent instance.

        Will first try get-next on {var}, then fall back to getting
        {var}.0 on failure.  This is to work around SNMP bugs observed in
        some agents  (Weathergoose).

        """
        oid = self.nodes[var].oid
        direct_oid = oid + OID('0')

        def format_get_result(result):
            if direct_oid in result:
                return result[direct_oid]

        def format_getnext_result(result):
            if result and hasattr(result, 'values'):
                return result.values()[0]
            else:
                raise ValueError("invalid result value", result)

        def format_result_keys(result):
            return dict((OID(k), v) for k, v in result.items())

        def use_get(failure):
            df = self.agent_proxy.get([str(direct_oid)])
            df.addCallback(format_result_keys)
            df.addCallback(format_get_result)
            return df

        df = self.agent_proxy.walk(str(oid))
        df.addCallback(format_getnext_result)
        df.addErrback(use_get)
        return df

    # pylint: disable=C0103

    def get_sysObjectID(self):
        """Retrieves the sysObjectID of the first agent instance."""
        return self._get_sysvariable('sysObjectID')

    def get_sysDescr(self):
        """Retrieves the sysDescr of the first agent instance."""
        return self._get_sysvariable('sysDescr')

    def get_sysUpTime(self):
        """Retrieves the sysUpTime of the first agent instance."""
        return self._get_sysvariable('sysUpTime')

    @defer.inlineCallbacks
    def get_gmtime_and_uptime(self):
        """Retrieves the agent's current sysUpTime and gets the current GMT time

        :returns: A tuple of (gmt_timestamp, collected_sysuptime)

        """
        sysuptime = yield self._get_sysvariable('sysUpTime')
        gmtime = time.mktime(time.gmtime())
        defer.returnValue((gmtime, sysuptime))

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

        :argument second_uptime: A (gmt_timestamp, sysUpTime) tuple. The
                                 timestamp should be the wall clock of the NAV
                                 server when the sysUpTime value was
                                 collected.

        :returns: The deviation, in seconds, between the collected uptime
        delta and the expected uptime delta.

        """
        tstamp1, uptime1 = first_uptime
        tstamp2, uptime2 = second_uptime

        expected_delta = (tstamp2 - tstamp1) * 100.0
        expected_uptime2 = (uptime1 + expected_delta) % 2**32
        deviation = (uptime2 - expected_uptime2) / 100.0
        return deviation

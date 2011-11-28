#
# Copyright (C) 2011 UNINETT AS
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
"""snmp check plugin"""

from twisted.internet import error, defer
from nav.ipdevpoll import Plugin

SYSTEM_OID = '.1.3.6.1.2.1.1'

class SnmpCheck(Plugin):
    """Checks that the device's SNMP agent is responding properly.

    This is done by attempting to retrieve the SNMPv2-MIB::system variables.
    If there is not response, an snmpAgentState (snmpAgentDown) event is
    dispatched.

    """

    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self._logger.debug("checking snmp agent availability")
        df = self.agent.getTable([SYSTEM_OID], maxRepetitions=1)
        df.addCallbacks(self._verify_result, self._handle_failure)
        return df

    def _verify_result(self, result):
        if not result:
            self._logger.debug("result was empty")
            self._mark_as_down()

    def _handle_failure(self, failure):
        failure.trap(defer.TimeoutError, error.TimeoutError)
        self._mark_as_down()

    def _mark_as_down(self):
        self._logger.warning("SNMP agent down on %s", self.netbox.sysname)

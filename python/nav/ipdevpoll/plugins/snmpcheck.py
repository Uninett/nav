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
from twisted.internet.defer import returnValue
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

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("snmp version from db: %s", self.netbox.snmp_version)

        version = 2
        is_ok = yield self._do_check(version)
        if not is_ok:
            version = 1
            is_ok = yield self._do_check(version)
        if not is_ok:
            returnValue(self._mark_as_down())
        else:
            returnValue(self._all_is_ok(version))

    @defer.inlineCallbacks
    def _do_check(self, version=2):
        self.agent.snmpVersion = 'v%s' % version
        self._logger.debug("checking SNMPv%s availability", version)
        try:
            result = yield self.agent.getTable([SYSTEM_OID], maxRepetitions=1)
        except (defer.TimeoutError, error.TimeoutError):
            self._logger.debug("SNMPv% timed out", version)
            returnValue(False)
        else:
            if not result:
                self._logger.debug("response was empty")
            returnValue(bool(result))

    def _mark_as_down(self):
        self._logger.warning("SNMP agent down on %s", self.netbox.sysname)

    def _all_is_ok(self, version):
        self._logger.debug("SNMPv%s response ok", version)

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

import datetime

from twisted.internet import error, defer
from twisted.internet.defer import returnValue

from nav.models.event import AlertHistory
from nav.ipdevpoll import Plugin

SYSTEM_OID = '.1.3.6.1.2.1.1'

class SnmpCheck(Plugin):
    """Checks that the device's SNMP agent is responding properly.

    This is done by attempting to retrieve the SNMPv2-MIB::system variables.
    If there is not response, an snmpAgentState (snmpAgentDown) event is
    dispatched.

    """
    down_set = None

    def __init__(self, *args, **kwargs):
        super(SnmpCheck, self).__init__(*args, **kwargs)
        if SnmpCheck.down_set is None:
            SnmpCheck.down_set = get_snmp_agent_down_set()

    @classmethod
    def can_handle(cls, netbox):
        return True

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("snmp version from db: %s", self.netbox.snmp_version)
        is_ok = yield self._do_check()

        if not is_ok:
            returnValue(self._mark_as_down())
        else:
            returnValue(self._mark_as_up())

    @defer.inlineCallbacks
    def _do_check(self):
        version = 2
        is_ok = yield self._check_version(version)
        if not is_ok:
            version = 1
            is_ok = yield self._check_version(version)
        returnValue(is_ok)

    @defer.inlineCallbacks
    def _check_version(self, version):
        self.agent.snmpVersion = 'v%s' % version
        self._logger.debug("checking SNMPv%s availability", version)
        try:
            result = yield self.agent.getTable([SYSTEM_OID], maxRepetitions=1)
        except (defer.TimeoutError, error.TimeoutError):
            self._logger.debug("SNMPv% timed out", version)
            returnValue(False)
        else:
            if result:
                self._logger.debug("SNMPv%s response ok", version)
            else:
                self._logger.debug("response was empty")
            returnValue(bool(result))

    def _mark_as_down(self):
        if self.netbox.id not in self.down_set:
            self._logger.warning("SNMP agent down on %s", self.netbox.sysname)
            self.down_set.add(self.netbox.id)

    def _mark_as_up(self):
        if self.netbox.id in self.down_set:
            self._logger.warning("SNMP agent up again on %s",
                                 self.netbox.sysname)
            self.down_set.remove(self.netbox.id)

def get_snmp_agent_down_set():
    """Returns a set of netbox ids where the SNMP agent is known to be down"""
    infinity = datetime.datetime.max
    down = AlertHistory.objects.filter(
        netbox__isnull=False, event_type__id='snmpAgentState',
        end_time__gte=infinity).values('netbox__id')
    down_set = set(row['netbox__id'] for row in down)
    return down_set

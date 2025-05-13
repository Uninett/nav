#
# Copyright (C) 2011, 2012, 2016, 2019 Uninett AS
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
"""snmp check plugin"""

from pynetsnmp.netsnmp import SnmpTimeoutError
from twisted.internet import error, defer

from django.db import transaction

from nav.event2 import EventFactory
from nav.models import manage, event
from nav.ipdevpoll import Plugin, db
from nav.ipdevpoll.jobs import SuggestedReschedule

SYSTEM_OID = '.1.3.6.1.2.1.1'
EVENT = EventFactory(
    'ipdevpoll', 'eventEngine', 'snmpAgentState', 'snmpAgentDown', 'snmpAgentUp'
)
INFO_KEY_NAME = 'status'
INFO_VARIABLE_NAME = 'snmpstate'


class SnmpCheck(Plugin):
    """Checks that the device's SNMP agent is responding properly.

    This is done by attempting to retrieve the SNMPv2-MIB::system variables.
    If there is no response, an snmpAgentState (snmpAgentDown) event is
    dispatched.

    """

    @classmethod
    def can_handle(cls, netbox):
        return netbox.is_up() and bool(netbox.snmp_parameters)

    def __init__(self, *args, **kwargs):
        super(SnmpCheck, self).__init__(*args, **kwargs)

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug(
            "snmp version from db: %s", self.netbox.snmp_parameters.version
        )
        was_down = yield db.run_in_thread(self._currently_down)
        is_ok = yield self._do_check()

        if is_ok and was_down:
            yield self._mark_as_up()
        elif not is_ok:
            # Always send down events; eventengine will ignore any duplicates
            yield self._mark_as_down()
            raise SuggestedReschedule(delay=60)

    @defer.inlineCallbacks
    def _do_check(self):
        self._logger.debug("checking SNMP v%s availability", self.agent.snmpVersion)
        try:
            result = yield self.agent.walk(SYSTEM_OID)
        except (defer.TimeoutError, error.TimeoutError, SnmpTimeoutError):
            self._logger.debug("SNMP v%s timed out", self.agent.snmpVersion)
            return False

        self._logger.debug("SNMP response: %r", result)
        return bool(result)

    @defer.inlineCallbacks
    def _mark_as_down(self):
        self._logger.warning("SNMP agent down on %s", self.netbox.sysname)
        yield db.run_in_thread(self._save_state, 'down')
        yield db.run_in_thread(self._dispatch_down_event)

    @defer.inlineCallbacks
    def _mark_as_up(self):
        self._logger.warning("SNMP agent up again on %s", self.netbox.sysname)
        yield db.run_in_thread(self._save_state, 'up')
        yield db.run_in_thread(self._dispatch_up_event)

    def _save_state(self, state):
        info, _ = manage.NetboxInfo.objects.get_or_create(
            netbox_id=self.netbox.id, key=INFO_KEY_NAME, variable=INFO_VARIABLE_NAME
        )
        info.value = state
        info.save()

    @transaction.atomic()
    def _dispatch_down_event(self):
        EVENT.start(None, self.netbox.id).save()

    @transaction.atomic()
    def _dispatch_up_event(self):
        EVENT.end(None, self.netbox.id).save()

    @transaction.atomic()
    def _currently_down(self):
        internally_down = manage.NetboxInfo.objects.filter(
            netbox=self.netbox.id,
            key=INFO_KEY_NAME,
            variable=INFO_VARIABLE_NAME,
            value="down",
        ).exists()
        globally_down = (
            event.AlertHistory.objects.unresolved("snmpAgentState")
            .filter(netbox=self.netbox.id)
            .exists()
        )

        return internally_down or globally_down

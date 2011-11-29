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

from twisted.internet import error, defer, threads
from twisted.internet.defer import returnValue

from nav.models.event import EventQueue as Event, EventQueueVar as EventVar
from nav.ipdevpoll.db import commit_on_success
from nav.models.event import AlertHistory
from nav.ipdevpoll import Plugin, get_class_logger
from nav.ipdevpoll.snmp import AgentProxy
from nav.ipdevpoll.jobs import SuggestedReschedule

SYSTEM_OID = '.1.3.6.1.2.1.1'

class SnmpCheck(Plugin):
    """Checks that the device's SNMP agent is responding properly.

    This is done by attempting to retrieve the SNMPv2-MIB::system variables.
    If there is no response, an snmpAgentState (snmpAgentDown) event is
    dispatched.

    """
    down_set = None

    def __init__(self, *args, **kwargs):
        super(SnmpCheck, self).__init__(*args, **kwargs)
        if SnmpCheck.down_set is None:
            SnmpCheck.down_set = get_snmp_agent_down_set()
            get_class_logger(SnmpCheck).debug("initially down: %r",
                                              SnmpCheck.down_set)

    @classmethod
    def can_handle(cls, netbox):
        return True

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("snmp version from db: %s", self.netbox.snmp_version)
        is_ok = yield self._do_check()

        if not is_ok:
            yield self._mark_as_down()
            raise SuggestedReschedule(60)
        else:
            yield self._mark_as_up()

    @defer.inlineCallbacks
    def _do_check(self):
        is_ok = yield self._check_version(2)
        if not is_ok:
            is_ok = yield self._check_version(1)
        returnValue(is_ok)

    @defer.inlineCallbacks
    def _check_version(self, version):
        version = 'v%s' % version
        if self.agent.snmpVersion != version:
            agent = self._get_alternate_agent(version)
        else:
            agent = self.agent

        self._logger.debug("checking SNMP%s availability", version)
        try:
            result = yield agent.walk(SYSTEM_OID)
        except (defer.TimeoutError, error.TimeoutError):
            self._logger.debug("SNMP%s timed out", version)
            returnValue(False)
        finally:
            if agent is not self.agent:
                agent.close()

        self._logger.debug("SNMP response: %r", result)
        returnValue(bool(result))


    def _get_alternate_agent(self, version):
        """Create an alternative Agent Proxy for our host.

        Return value is an AgentProxy object created with the same
        parameters as the controlling job handler's AgentProxy, but
        with a different SNMP version.

        """
        old_agent = self.agent
        agent = AgentProxy(
            old_agent.ip, old_agent.port,
            community=old_agent.community,
            snmpVersion = version)
        if hasattr(old_agent, 'protocol'):
            agent.protocol = old_agent.protocol

        agent.open()
        return agent

    @defer.inlineCallbacks
    def _mark_as_down(self):
        if self.netbox.id not in self.down_set:
            self._logger.warning("SNMP agent down on %s", self.netbox.sysname)
            self.down_set.add(self.netbox.id)
            yield threads.deferToThread(self._dispatch_down_event)

    @defer.inlineCallbacks
    def _mark_as_up(self):
        if self.netbox.id in self.down_set:
            self._logger.warning("SNMP agent up again on %s",
                                 self.netbox.sysname)
            self.down_set.remove(self.netbox.id)
            yield threads.deferToThread(self._dispatch_up_event)

    @commit_on_success
    def _dispatch_down_event(self):
        event = self._make_snmpagentstate_event()
        event.state = event.STATE_START
        event.save()
        var = EventVar(event_queue=event,
                       variable='alerttype', value='snmpAgentDown')
        var.save()

    @commit_on_success
    def _dispatch_up_event(self):
        event = self._make_snmpagentstate_event()
        event.state = event.STATE_END
        event.save()
        var = EventVar(event_queue=event,
                       variable='alerttype', value='snmpAgentUp')
        var.save()

    def _make_snmpagentstate_event(self):
        event = Event()
        # FIXME: ipdevpoll is not a registered subsystem in the database yet
        event.source_id = 'getDeviceData'
        event.target_id = 'eventEngine'
        event.device_id = self.netbox.device.id
        event.netbox_id = self.netbox.id
        event.event_type_id = 'snmpAgentState'
        return event

@commit_on_success
def get_snmp_agent_down_set():
    """Returns a set of netbox ids where the SNMP agent is known to be down"""
    infinity = datetime.datetime.max
    down = AlertHistory.objects.filter(
        netbox__isnull=False, event_type__id='snmpAgentState',
        end_time__gte=infinity).values('netbox__id')
    down_set = set(row['netbox__id'] for row in down)
    return down_set

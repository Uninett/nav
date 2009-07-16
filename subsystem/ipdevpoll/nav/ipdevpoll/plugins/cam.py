# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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

from twisted.internet import defer, threads, reactor
from twisted.python.failure import Failure
from twistedsnmp import snmpprotocol, agentproxy

from nav.mibs.bridge_mib import BridgeMib
from nav.mibs.cisco_vtp_mib import CiscoVTPMib
from nav.mibs.if_mib import IfMib
from nav.mibs.entity_mib import EntityMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage
from nav.models import manage
from nav.util import round_robin

class Cam(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    @defer.deferredGenerator
    def handle(self):
        self.logger.debug("Collecting CAM logs")
        agents = CommunityIndexAgentProxy(self.netbox)

        interfaces = manage.Interface.objects.filter(
            netbox__id=self.netbox.id)
        dw = defer.waitForDeferred(threads.deferToThread(
            storage.shadowify_queryset, interfaces))
        yield dw
        result = dw.getResult()

        vlans = []
        for i in result:
            if i.vlan and i.vlan not in vlans:
                vlans.append(i.vlan)

        bridge_mib = BridgeMib(self.job_handler.agent)
        if_mib = IfMib(self.job_handler.agent)

        defer.setDebugging(True)
        mac_result = []
        if len(vlans) > 0:
            for vlan in vlans:
                agent = agents.agent_for_vlan(vlan)
                vlan_bridge_mib = BridgeMib(agent)
                df = vlan_bridge_mib.retrieve_columns([
                    'dot1dTpFdbAddress',
                    'dot1dTpFdbPort',
                    ])
                dw = defer.waitForDeferred(df)
                yield dw
                try:
                    result = dw.getResult()
                except defer.TimeoutError, e:
                    self.logger.warning("Timeout for vlan %d" % vlan)
                    continue
                else:
                    self.logger.debug("Found %d results for vlan %d" % (
                        len(result), vlan))
                    mac_result.append(result)

        # FIXME just run the regular one without community string indexing
        # anyways?
        if len(mac_result) == 0 or len(vlans) == 0:
            self.logger.debug("Trying to fetch cam without community index")
            dw = defer.waitForDeferred(
                bridge_mib.retrieve_columns([
                    'dot1dTpFdbAddress',
                    'dot1dTpFdbPort',
                ]))
            yield dw
            result = dw.getResult()
            mac_result = [result]
            self.logger.debug("Found %d results for box" % len(result))

        #dw = defer.waitForDeferred(
        #    bridge_mib.retrieve_column('dot1dBasePortIfIndex'))
        #yield dw
        #ifindex_result = dw.getResult()

        #dw = defer.waitForDeferred(
        #    if_mib.retrieve_column('ifName'))
        #yield dw
        #ifname_result = dw.getResult()

        yield True

class CommunityIndexAgentProxy(object):
    def __init__(self, netbox):
        self.netbox = netbox
        self.ports = round_robin([snmpprotocol.port() for i in range(10)])

    def agent_for_vlan(self, vlan):
        community = "%s@%s" % (self.netbox.read_only, vlan)
        port = self.ports.next()
        agent = agentproxy.AgentProxy(
            self.netbox.ip, 161,
            community=community,
            snmpVersion='v%s' % self.netbox.snmp_version,
            protocol=port.protocol,
        )
        return agent

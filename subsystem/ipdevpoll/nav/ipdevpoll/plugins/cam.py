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

import re

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.mibs.qbridge_mib import QBridgeMib
from nav.mibs.cisco_vtp_mib import CiscoVTPMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage
from nav.models.manage import Interface
from schedule import ports

class Cam(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    @defer.deferredGenerator
    def handle(self):
        self.logger.debug("Collecting CAM logs")

        dw = defer.waitForDeferred(threads.deferToThread(
                storage.shadowify_queryset, manage.Vlan.objects.all()))
        yield dw
        vlans = dw.getResult()

        result = None
        if len(vlans) > 0:
            dw = defer.waitForDeferred(threads.deferToThread(
                self._fetch_macs_for_vlans(vlans)))
            yield dw
            mac_result = dw.getResult()

        # FIXME just run the regular one without community string indexing
        # anyways?
        if len(mac_result) == 0 or len(vlans) == 0:
            bridge_mib = BridgeMib(self.job_handler.agent)
            dw = defer.waitForDeferred(bridge_mib.retrieve_columns([
                    'dot1dTpFdbAddress',
                    'dot1dTpFdbPort',
                ]))
            yield dw
            mac_result = dw.getResult()

        dw = defer.waitForDeferred(bridge_mib.retrieve_column(
                'dot1dBasePortIfIndex'
            ))
        yield dw
        ifindex_result = dw.getResult()

        yield True

    def _fetch_macs_for_vlans(self, vlans):
        vlans = iter(vlans)
        final_result = []
        deferred_result = defer.Deferred()

        def format_result(result, vlan):
            for index, row in result.items():
                final_result.append({
                        'vlan': vlan,
                        'mac': row['dot1dTpFdbAddress'],
                        'port': row['dot1dTpFdbPort'],
                    })
            return True

        def schedule_next():
            try:
                vlan = vlans.next()
            except StopIteration:
                deferred_result.callback(final_result)
                return

            community = self.netbox.read_only + vlan
            port = ports.next()
            agent = agentproxy.AgentProxy(
                self.netbox.ip, 161,
                community=community
                snmpVersion='v%s' % self.netbox.snmp_version,
                protocol=port.protocol,
            )
            bridge_mib = BridgeMib(agent)

            df = bridge_mib.retrieve_columns([
                    'dot1dTpFdbAddress',
                    'dot1dTpFdbPort',
                ])
            df.addCallback(format_result, vlan)
            df.addCallback(schedule_next)

        reactor.callLater(0, schedule_next)
        return deferred_result

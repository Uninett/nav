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
"""ipdevpoll plugin to pull vlan information.

Just a prototype, will only log info, not store it in NAVdb.

"""

import re

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.mibs import QBridgeMib, CiscoVTPMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage
from nav.models.manage import Interface

VLAN_REGEXP = re.compile('Vlan(\d+)')

class Vlans(Plugin):
    """
    ipdevpoll-plugin for collecting vlan information from monitored
    equipment.

    Tries to retrieve information with Q-BRIDGE-MIB before trying
    vendor specific retrieval methods
    """
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        """
        This plugin handles netboxes
        """
        return True

    @defer.deferredGenerator
    def handle(self):
        """
        Plugin entrypoint
        """

        self.logger.debug("Deriving VLAN information from ifdecsr fields on known interfaces")
        df = threads.deferToThread(self.get_interfaces)
        dw = defer.waitForDeferred(df)
        yield dw

        interfaces = dw.getResult()
        for interface in interfaces:
            data = VLAN_REGEXP.findall(interface.ifdescr)
            if data:
                if interface.vlan and str(interface.vlan) != str(data[0]):
                    self.logger.warning("Interface descr does not match assigned vlan" + \
                        " %s , %s != %s" % (interface, interface.vlan, data[0]))
                elif not interface.vlan:
                    interface.vlan = data[0]

        self.logger.debug("Collecting VLAN information from interfaces using SNMP")
        qbridgemib = QBridgeMib(self.job_handler.agent)
        df = qbridgemib.retrieve_column('dot1qPvid')
        dw = defer.waitForDeferred(df)
        yield dw

        result = dw.getResult()

        if result:
            result = [(ifindex, vlan) for (ifindex,), vlan in result.items()]
        else:
            self.logger.debug("Collecting VLAN information using CISCO-VTP-MIB")
            ciscovtpmib = CiscoVTPMib(self.job_handler.agent)
            df = ciscovtpmib.retrieve_column('vtpVlanIfIndex')
            dw = defer.waitForDeferred(df)
            yield dw
            result = dw.getResult()

            if not result:
                return

            result = [(ifindex, vlan) for (_, vlan), ifindex in result.items()]

        netbox = self.job_handler.container_factory(storage.Netbox, key=None)
        for (ifindex, vlan) in result:
            interface = self.job_handler.container_factory(storage.Interface, key=ifindex)
            interface.netbox = netbox
            interface.vlan = vlan

    def error(self, failure):
        """
        Return a failure to the ipdevpoll-deamon
        """
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)

    def get_interfaces(self):
        netbox = self.job_handler.container_factory(storage.Netbox, key=None).get_model()
        query = Interface.objects.filter(netbox=netbox)
        return storage.shadowify_queryset(query)

    @staticmethod
    def vlan_port_list_parser(octet_string):
        """
        Returns a list of ports with the given vlan from
        Q-BRIDGE-MIB::dot1qVlanCurrentEgressPorts.
        This provides both tagged and untagged vlans.
        """
        if not octet_string:
            return []
        ret = []
        for octet in octet_string.split(' '):
            ret.append("".join([str((int(octet, 16) >> y) & 1) for y in range(7, -1, -1)]))
        return [b[0]+1 for b in enumerate([a for a in "".join(ret)]) if b[1] == '1']




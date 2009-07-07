# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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

import logging

from twisted.internet import defer
from twisted.python.failure import Failure

from nav.mibs import IpMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage

class Arp(Plugin):
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        if netbox.category.is_gw() or netbox.category.is_gsw():
            return True
        else:
            return False

    def handle(self):
        self.logger.debug("Collecting ARP data")
        self.ipmib = IpMib(self.job_handler.agent)
        df = self.ipmib.retrieve_columns([
            'ipNetToMediaPhysAddress',
            'ipNetToMediaNetAddress',
        ])
        df.addCallback(self.got_arp)
        self.addErrback(self.error)

    # FIXME Copypasta from vlan plugin
    def error(self, failure):
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)

    def timeout_arp(self, result):
        if storage.Arp in self.job_handler.containers:
            for arp in result:
                key = (arp.ip, arp.mac)
                if not key in self.job_handler.containers[storage.Arp]:
                    arp.end_time = datetime.today()
        self.deferred.callback(True)
        return result

    def got_arp(self, result):
        self.logger.debug("Found %d ARP entries" % len(result))

        if len(result) == 0:
            # Do Cisco stuff
            self.logger.debug("No ARP entries found. Trying vendor specific MIBs")
            return

        netbox = self.job_handler.container_factory(storage.Netbox, key=None)
        netbox.arp_set = []
        for (ifIndex,), row in result.items():
            ip = row['ipNetToMediaNetAddress']
            mac = row['ipNetToPhysAddress']

            arp = self.job_handler.container_factory(storage.Arp, key=(
                ip,
                mac,
            ))
            #arp.prefix = Something
            arp.sysname = netbox.sysname
            arp.ip = ip
            arp.mac = mac

            netbox.arp_set.append(arp)

        existing_arp = manage.Arp.objects.filter(
            netbox=netbox,
            end_time__gt=datetime.max,
        )
        df = threads.deferToThread(storage.shadowify_queryset, existing_arp)
        df.addCallback(timeout_arp)
        return result

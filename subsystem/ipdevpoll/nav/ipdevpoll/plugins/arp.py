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
from datetime import datetime

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.mibs import IpMib
from nav.models import manage
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage

class Arp(Plugin):
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        if netbox.category.id == 'GW' or \
                netbox.category.id == 'GSW':
            return True
        else:
            return False

    def handle(self):
        self.logger.debug("Collecting ARP data")
        netbox = self.job_handler.container_factory(storage.Netbox, key=None)
        netbox_from_db = manage.Netbox.objects.get(id=netbox.id)
        df = threads.deferToThread(storage.shadowify, netbox_from_db)
        df.addCallback(self.got_netbox)
        df.addErrback(self.error)
        return self.deferred

    # FIXME Copypasta from vlan plugin
    def error(self, failure):
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)

    def got_netbox(self, result):
        self.logger.debug('Got netbox: %s' % result.sysname)
        self.ipmib = IpMib(self.job_handler.agent)
        df = self.ipmib.retrieve_columns([
            'ipNetToMediaPhysAddress',
            'ipNetToMediaNetAddress',
        ])
        df.addCallback(self.got_arp, netbox=result)

    def got_arp(self, result, netbox=None):
        self.logger.debug("Found %d ARP entries" % len(result))

        if len(result) == 0:
            # Do Cisco stuff
            self.logger.debug("No ARP entries found. Trying vendor specific MIBs")
            return

        new_arp = {}
        for key, row in result.items():
            ip = row['ipNetToMediaNetAddress']
            mac = binary_mac_to_hex(row['ipNetToMediaPhysAddress'])

            arp = self.job_handler.container_factory(storage.Arp, key=(
                ip,
                mac,
            ))
            #arp.prefix = Something
            arp.sysname = netbox.sysname
            arp.ip = ip
            arp.mac = mac
            arp.netbox = netbox
            arp.start_time = datetime.utcnow()
            arp.end_time = datetime.max

            new_arp[(ip, mac)] = arp

        existing_arp = manage.Arp.objects.filter(
            netbox__id=netbox.id,
            end_time=datetime.max,
        )
        df = threads.deferToThread(storage.shadowify_queryset, existing_arp)
        df.addCallback(self.timeout_arp, new_records=new_arp)
        df.addErrback(self.error)
        return result

    def timeout_arp(self, result, new_records=None):
        for row in result:
            key = (row.ip, row.mac)
            if key not in new_records:
                self.logger.debug('%s for %s was not found on netbox' % key)
                arp = self.job_handler.container_factory(storage.Arp, key=key)

                arp.ip = row.ip
                arp.mac = row.mac
                arp.end_time = datetime.utcnow()
        self.deferred.callback(True)
        return result

def binary_mac_to_hex(binary_mac):
    """Convert a binary string MAC address to hex string."""
    if binary_mac:
        return ":".join("%02x" % ord(x) for x in binary_mac)

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
"""ipdevpoll plugin to collect interface data.

This plugin will also examine the list of know interfaces for a netbox
and compare it to the collected list.  Any known interface not found
by polling will be marked as missing with a timestamp (gone_since).
"""

import logging
import pprint
import datetime

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.mibs.if_mib import IfMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage
from nav.ipdevpoll.utils import binary_mac_to_hex
from nav.models import manage

class Interfaces(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self.logger.debug("Collecting interface data")
        self.ifmib = IfMib(self.job_handler.agent)
        df = self.ifmib.retrieve_columns([
                'ifDescr',
                'ifType',
                'ifSpeed',
                'ifPhysAddress',
                'ifAdminStatus',
                'ifOperStatus',
                'ifName',
                'ifHighSpeed',
                'ifConnectorPresent',
                'ifAlias',
                ])
        df.addCallback(self._got_interfaces)
        df.addCallback(self._check_missing_interfaces)
        df.addErrback(self._error)
        return df

    def _error(self, failure):
        """Errback for SNMP failures."""
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)

    def _got_interfaces(self, result):
        """Process the list of collected interfaces."""

        self.logger.debug("Found %d interfaces", len(result))

        # Now save stuff to containers and pass the list of containers
        # to the next callback
        netbox = self.job_handler.container_factory(storage.Netbox, key=None)
        interfaces = [self._convert_row_to_container(netbox, ifindex, row)
                      for (ifindex,),row in result.items()]
        return interfaces
    
    def _convert_row_to_container(self, netbox, ifindex, row):
        """Convert a collected ifTable/ifXTable row into a container object."""

        interface = self.job_handler.container_factory(storage.Interface,
                                                       key=ifindex)
        interface.ifindex = ifindex
        interface.ifdescr = row['ifDescr']
        interface.iftype = row['ifType']

        # ifSpeed spec says to use ifHighSpeed if the 32-bit unsigned
        # integer is maxed out
        if row['ifSpeed'] < 4294967295:
            interface.speed = row['ifSpeed'] / 1000000.0
        else:
            interface.speed = float(row['ifHighSpeed'])

        interface.ifphysaddress = binary_mac_to_hex(row['ifPhysAddress'])
        interface.ifadminstatus = row['ifAdminStatus']
        interface.ifoperstatus = row['ifOperStatus']

        interface.ifname = row['ifName']
        interface.ifconnectorpresent = row['ifConnectorPresent'] == 1
        interface.ifalias = row['ifAlias']
        
        interface.gone_since = None

        interface.netbox = netbox
        return interface

    def _check_missing_interfaces(self, interfaces):
        """Check if any known interfaces are missing from a result set.

        This method will load the known interfaces of this netbox from
        the database.  A new container will be created for any known
        interface missing from the result set, and its gone_since
        timestamp will be set.

        NOTE: The comparisons are only made using ifindex values.  If
        a netbox has re-assigned ifindices to its interfaces since the
        last collection, this may cause trouble.

        TODO: Make a deletion algorithm.  Missing interfaces that do
        not correspond to a module known to be down should be deleted.
        If all interfaces belonging to a specific module is down, we
        may have detected that the module is down as well.

        """
        def mark_as_gone(ifindices):
            now = datetime.datetime.now()
            netbox = self.job_handler.container_factory(storage.Netbox, 
                                                        key=None)

            if ifindices:
                self.logger.info("Marking interfaces as gone.  Ifindex: %r", 
                                 ifindices)

            for ifindex in ifindices:
                interface = self.job_handler.container_factory(
                    storage.Interface, key=ifindex)
                interface.ifindex = ifindex
                interface.gone_since = now
                interface.netbox = netbox

        def do_comparison(known_interfaces):
            known_ifindices = set(i.ifindex for i in known_interfaces)
            found_ifindices = set(i.ifindex for i in interfaces)
            missing_ifindices = known_ifindices.difference(found_ifindices)

            mark_as_gone(missing_ifindices)

            # This should be the end of the deferred chain
            return True
            
        # pick only the ones not known to be missing already
        queryset = manage.Interface.objects.filter(netbox=self.netbox.id,
                                                   gone_since__isnull=True)
        deferred = threads.deferToThread(storage.shadowify_queryset, 
                                         queryset)
        deferred.addCallback(do_comparison)
        return deferred

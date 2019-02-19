# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2012 Uninett AS
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
"""ipdevpoll plugin to collect interface data.

The plugin uses IF-MIB to retrieve generic interface data, and
EtherLike-MIB to retrieve duplex status for ethernet interfaces.

"""
from twisted.internet import defer

from nav.Snmp import safestring
from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib
from nav.mibs.etherlike_mib import EtherLikeMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.utils import binary_mac_to_hex
from nav.models import manage

DUPLEX_MAP = {
    'unknown': None,
    'halfDuplex': manage.Interface.DUPLEX_HALF,
    'fullDuplex': manage.Interface.DUPLEX_FULL,
}


class Interfaces(Plugin):
    "Collects comprehensive information about device's network interfaces"
    def __init__(self, *args, **kwargs):
        super(Interfaces, self).__init__(*args, **kwargs)
        self.ifmib = IfMib(self.agent)
        self.etherlikemib = EtherLikeMib(self.agent)

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("Collecting interface data")
        df = self._get_iftable_columns()
        df.addCallback(self._retrieve_duplex)
        df.addCallback(self._process_interfaces)
        df.addCallback(self._get_stack_status)
        yield df
        shadows.Interface.add_sentinel(self.containers)

    def _get_iftable_columns(self):
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
        return df.addCallback(reduce_index)

    def _process_interfaces(self, result):
        """Process the list of collected interfaces."""

        self._logger.debug("Found %d interfaces", len(result))

        # Now save stuff to containers and pass the list of containers
        # to the next callback
        netbox = self.containers.factory(None, shadows.Netbox)
        interfaces = [self._convert_row_to_container(netbox, ifindex, row)
                      for ifindex, row in result.items()]
        return interfaces

    def _convert_row_to_container(self, netbox, ifindex, row):
        """Convert a collected ifTable/ifXTable row into a container object."""

        interface = self.containers.factory(ifindex, shadows.Interface)
        interface.ifindex = ifindex
        interface.ifdescr = row['ifDescr']
        interface.iftype = row['ifType']

        # ifSpeed spec says to use ifHighSpeed if the 32-bit unsigned
        # integer is maxed out
        if row['ifSpeed'] is not None and row['ifSpeed'] < 4294967295:
            interface.speed = row['ifSpeed'] / 1000000.0
        elif row['ifHighSpeed'] is not None:
            interface.speed = float(row['ifHighSpeed'])

        interface.ifphysaddress = binary_mac_to_hex(row['ifPhysAddress'])
        interface.ifadminstatus = row['ifAdminStatus']
        interface.ifoperstatus = row['ifOperStatus']

        interface.ifname = row['ifName'] or interface.baseport or row['ifDescr']
        interface.ifconnectorpresent = row['ifConnectorPresent'] == 1
        interface.ifalias = safestring(row['ifAlias'])

        # Set duplex if sucessfully retrieved
        if 'duplex' in row and row['duplex'] in DUPLEX_MAP:
            interface.duplex = DUPLEX_MAP[row['duplex']]

        interface.gone_since = None

        interface.netbox = netbox
        return interface

    @defer.inlineCallbacks
    def _get_stack_status(self, interfaces):
        """Retrieves data from the ifStackTable and initiates a search for a
        proper ifAlias value for those interfaces that lack it.

        """
        def _stackify(stackstatus):
            ifindex_map = dict((ifc.ifindex, ifc) for ifc in interfaces)
            stack = [(ifindex_map[higher], ifindex_map[lower])
                     for higher, lower in stackstatus
                     if higher in ifindex_map and lower in ifindex_map]
            return stack

        stack = yield self.ifmib.get_stack_status().addCallback(_stackify)
        self._get_ifalias_from_lower_layers(stack)
        self._create_stack_containers(stack)
        defer.returnValue(interfaces)

    def _get_ifalias_from_lower_layers(self, stack):
        """For each interface without an ifAlias value, attempts to find
        ifAlias from a lower layer interface.

        By popular convention, some devices are configured with virtual router
        ports that are conceptually a layer above the physical interface.  The
        virtual port may have no ifAlias value, but the physical interface may
        have.  We want an ifAlias value, since it tells us the netident of the
        router port's network.

        """
        for higher, lower in stack:
            if not higher.ifalias and lower.ifalias:
                higher.ifalias = lower.ifalias
                self._logger.debug("%s alias set from lower layer %s: %s",
                                   higher.ifname, lower.ifname, higher.ifalias)

    def _create_stack_containers(self, stacklist):
        for higher, lower in stacklist:
            key = higher.ifindex, lower.ifindex
            stack = self.containers.factory(key, shadows.InterfaceStack)
            stack.higher = higher
            stack.lower = lower

    def _retrieve_duplex(self, interfaces):
        """Get duplex from EtherLike-MIB and update the ifTable results."""
        def update_result(duplexes):
            self._logger.debug("Got duplex information: %r", duplexes)
            for index, duplex in duplexes.items():
                if index in interfaces:
                    interfaces[index]['duplex'] = duplex
            return interfaces

        deferred = self.etherlikemib.get_duplex()
        deferred.addCallback(update_result)
        return deferred

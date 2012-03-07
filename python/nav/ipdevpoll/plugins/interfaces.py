# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2012 UNINETT AS
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

The plugin uses IF-MIB to retrieve generic interface data, and
EtherLike-MIB to retrieve duplex status for ethernet interfaces.

"""

from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib
from nav.mibs.etherlike_mib import EtherLikeMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.utils import binary_mac_to_hex

class Interfaces(Plugin):
    def handle(self):
        self._logger.debug("Collecting interface data")
        self.ifmib = IfMib(self.agent)
        self.etherlikemib = EtherLikeMib(self.agent)
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
        df.addCallback(reduce_index)
        df.addCallback(self._retrieve_duplex)
        df.addCallback(self._got_interfaces)
        df.addCallback(self._get_stack_status)
        return df

    def _got_interfaces(self, result):
        """Process the list of collected interfaces."""

        self._logger.debug("Found %d interfaces", len(result))

        # Now save stuff to containers and pass the list of containers
        # to the next callback
        netbox = self.containers.factory(None, shadows.Netbox)
        interfaces = [self._convert_row_to_container(netbox, ifindex, row)
                      for ifindex, row in result.items()]
        return interfaces
    
    duplex_map = {
        'unknown': None,
        'halfDuplex': 'h',
        'fullDuplex': 'f',
        }
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
        interface.ifalias = decode_to_unicode(row['ifAlias'])
        
        # Set duplex if sucessfully retrieved
        if 'duplex' in row and row['duplex'] in self.duplex_map:
            interface.duplex = self.duplex_map[ row['duplex'] ]

        interface.gone_since = None

        interface.netbox = netbox
        return interface

    def _get_stack_status(self, interfaces):
        """Retrieves data from the ifStackTable and initiates a search for a
        proper ifAlias value for those interfaces that lack it.
        
        """
        df = self.ifmib.retrieve_columns(['ifStackStatus'])
        df.addCallback(self._get_ifalias_from_lower_layers, interfaces)
        return df

    def _get_ifalias_from_lower_layers(self, stackstatus, interfaces):
        """For each interface without an ifAlias value, attempts to find
        ifAlias from a lower layer interface.

        By popular convention, some devices are configured with virtual router
        ports that are conceptually a layer above the physical interface.  The
        virtual port may have no ifAlias value, but the physical interface may
        have.  We want an ifAlias value, since it tells us the netident of the
        router port's network.
        
        """
        layer_map = {}        
        for (upper, lower), row in stackstatus.items():
            if upper > 0 and lower > 0:
                layer_map[upper] = lower

        ifindex_map = {}
        for interface in interfaces:
            ifindex_map[interface.ifindex] = interface

        for interface in interfaces:
            if interface.ifalias or interface.ifindex not in layer_map:
                continue
            lower_ifindex = layer_map[interface.ifindex]
            if lower_ifindex in ifindex_map:
                ifalias = ifindex_map[lower_ifindex].ifalias
                if ifalias:
                    interface.ifalias = ifalias
                    self._logger.debug("%s alias set from lower layer %s: %s",
                                       interface.ifname,
                                       ifindex_map[lower_ifindex].ifname,
                                       ifalias)

        return interfaces

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

def decode_to_unicode(string):
    if string is None:
        return
    try:
        return string.decode('utf-8')
    except UnicodeDecodeError:
        return string.decode('latin-1')
    except AttributeError:
        return unicode(string)

# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 UNINETT AS
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
"""ipdevpoll plugin to collect 802.1q VLAN information.

BRIDGE-MIB and Q-BRIDGE-MIB are used as sources for this plugin.
BRIDGE-MIB is used purely to collect a translation map between
ifindexes from IF-MIB and the port numbers used internally in BRIDGE
and Q-BRIDGE.

Specifically, this plugin will set the vlan and trunk attributes for
interfaces, as well as set the list of enabled VLANs on trunks.

"""

import re
import math

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.bitvector import BitVector
from nav.mibs import reduce_index
from nav.mibs.bridge_mib import BridgeMib
from nav.mibs.qbridge_mib import QBridgeMib, PortList
from nav.ipdevpoll import Plugin 
from nav.ipdevpoll import storage, shadows
from nav.models.manage import Interface


class Dot1q(Plugin):
    """Collect 802.1q info from BRIDGE and Q-BRIDGE MIBs."""

    @classmethod
    def can_handle(cls, netbox):
        """This plugin handles netboxes"""
        return True

    def handle(self):
        """Plugin entrypoint"""

        self._logger.debug("Collecting 802.1q VLAN information")

        self.bridgemib = BridgeMib(self.agent)
        self.qbridgemib = QBridgeMib(self.agent)
        
        # We first need the baseport list to translate port numbers to
        # ifindexes
        deferred = self.bridgemib.retrieve_column('dot1dBasePortIfIndex')
        deferred.addCallback(reduce_index)
        deferred.addCallback(self._get_pvids)
        #deferred.addCallback(self._get_trunkports)
        return deferred

    def _get_pvids(self, baseports):
        """Initiate collection of the current vlan config."""
        deferred = self.qbridgemib.retrieve_column('dot1qPvid')
        deferred.addCallback(reduce_index)
        deferred.addCallback(self._process_pvids, baseports)
        return deferred

    def _process_pvids(self, pvids, baseports):
        """Process the list of collected port/PVID mappings.

        If no PVID data was found, it is assumed that this bridge
        either does not support Q-BRIDGE-MIB or does not support
        802.1.q, and the plugin exits.

        If we did find some data, proceed to retrieve information
        about trunks (ports transmitting and receiving tagged ethernet
        frames).

        """

        self._logger.debug("PVID mapping: %r", pvids)
        if not pvids:
            return
        else:
            for port, pvid in pvids.items():
                if port in baseports:
                    ifindex = baseports[port]
                    interface = self.containers.factory(ifindex,
                                                        shadows.Interface)
                    interface.vlan = pvid
                else:
                    self._logger.info("dot1qPortVlanTable referred to unknown "
                                     "port number %s", port)

            deferred = self.qbridgemib.retrieve_columns((
                'dot1qVlanCurrentEgressPorts', 
                'dot1qVlanCurrentUntaggedPorts',
                ))
            deferred.addCallback(self._process_trunkports, baseports)
            return deferred

    def _process_trunkports(self, vlans, baseports):
        """Process a result from the dot1qVlanCurrentTable.

        The set of untagged ports is subtracted from the total set of
        egress ports for each vlan, resulting in a set of ports that
        transmit and receive tagged frames for this vlan (i.e. trunk
        ports).

        The first index element of this table is a TimeFilter, so we
        try to prune old rows and only use the most recent one for
        each VlanIndex.

        """
        
        # First prune the result table. We're not particularly
        # interested in the actual value of the time_index, we just
        # want to have the rows with the highest time_index for each
        # vlan_index.
        for index in sorted(vlans.keys()):
            time_index, vlan_index = index
            vlans[vlan_index] = vlans[index]
            del vlans[index]

        # Map trunk ports and their VLANs
        trunkports = {}
        for vlan, row in vlans.items():
            egress = PortList(row['dot1qVlanCurrentEgressPorts'])
            untagged = PortList(row['dot1qVlanCurrentUntaggedPorts'])
            try:
                tagged = egress - untagged
            except ValueError:
                self._logger.error("vlan %s subtraction mismatch between "
                                   "EgressPorts and UntaggedPorts", vlan)
                self._logger.debug("vlan: %s egress: %r untagged: %r",
                                   vlan, egress, untagged)
            else:
                for port in tagged.get_ports():
                    if port not in trunkports:
                        trunkports[port] = [vlan]
                    else:
                        trunkports[port].append(vlan)

        self._logger.debug("trunkports: %r", trunkports)

        # Now store it
        for port, vlans in trunkports.items():
            if port in baseports:
                # Mark as trunk
                ifindex = baseports[port]
                interface = self.containers.factory(ifindex,
                                                    shadows.Interface)
                interface.trunk = True

                # Store a hex string representation of enabled VLANs
                # in swportallowedvlan
                allowed = self.containers.factory(ifindex,
                                                 shadows.SwPortAllowedVlan)
                allowed.interface = interface
                allowed.hex_string = vlan_list_to_hex(vlans)

            else:
                self._logger.info("dot1qVlanCurrentTable referred to unknown "
                                  "port number %s", port)
            

def vlan_list_to_hex(vlans):
    """Convert a list of VLAN numbers to a hexadecimal string.

    The hexadecimal string is suitable for insertion into the
    swportallowedvlan table.
    """
    # Make sure there are at least 256 digits (128 octets) in the
    # resulting hex string.  This is necessary for parts of NAV to
    # parse the hexstring correctly.
    max_vlan = sorted(vlans)[-1]
    needed_octets = int(math.ceil((max_vlan+1) / 8.0))
    bits = BitVector('\x00' * max(needed_octets, 128))
    for vlan in vlans:
        bits[vlan] = True
    return bits.to_hex()

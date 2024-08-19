#
# Copyright (C) 2009-2012 Uninett AS
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
"""ipdevpoll plugin to collect 802.1q VLAN information.

BRIDGE-MIB and Q-BRIDGE-MIB are used as sources for this plugin.
BRIDGE-MIB is used purely to collect a translation map between
ifindexes from IF-MIB and the port numbers used internally in BRIDGE
and Q-BRIDGE.

Specifically, this plugin will set the vlan and trunk attributes for
interfaces, as well as set the list of enabled VLANs on trunks.

"""

from collections import defaultdict

from twisted.internet.defer import inlineCallbacks

from nav.util import mergedicts
from nav.mibs.bridge_mib import BridgeMib
from nav.mibs.qbridge_mib import QBridgeMib
from nav.models.manage import SwPortAllowedVlan
from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows


class Dot1q(Plugin):
    """Collect 802.1q info from BRIDGE and Q-BRIDGE MIBs."""

    baseports = {}
    pvids = {}

    def __init__(self, *args, **kwargs):
        super(Dot1q, self).__init__(*args, **kwargs)
        self.bridgemib = BridgeMib(self.agent)
        self.qbridgemib = QBridgeMib(self.agent)

    def _remap_vlan(self, vlan_ident):
        """Hook-in for subclasses to remap VLAN numbers if necessary"""
        return vlan_ident

    @inlineCallbacks
    def handle(self):
        """Collects VLAN configuration using Q-BRIDGE-MIB.

        If no PVID information can be found in Q-BRIDGE, the plugin assumes
        the device either doesn't support Q-BRIDGE or doesn't support 802.1q
        and exits.

        """
        self._logger.debug("Collecting 802.1q VLAN information")

        self.baseports = yield self.bridgemib.get_baseport_ifindex_map()
        self.pvids = yield self.qbridgemib.get_baseport_pvid_map()
        if self.pvids:
            self._process_pvids()
        else:
            return

        yield self._get_vlan_names()
        yield self._get_tagging_info()

    def _process_pvids(self):
        """Process the list of collected port/PVID mappings.

        If no PVID data was found, it is assumed that this bridge
        either does not support Q-BRIDGE-MIB or does not support
        802.1q, and the plugin exits.

        """
        self._logger.debug("PVID mapping: %r", self.pvids)

        for port, pvid in self.pvids.items():
            self._set_port_pvid(port, pvid)

    def _set_port_pvid(self, port, pvid):
        if port in self.baseports:
            ifindex = self.baseports[port]
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.vlan = pvid
            interface.trunk = False  # default all ports to non-tagging at first
        else:
            self._logger.debug("saw reference to non-existant baseport %s", port)

    @inlineCallbacks
    def _get_tagging_info(self):
        """Retrieves and processes information about VLAN egress ports and
        tagging.

        The set of untagged ports is subtracted from the total set of
        egress ports for each vlan, resulting in a set of ports that
        transmit and receive tagged frames for this vlan (i.e. trunk
        ports).

        """
        egress, untagged = yield self._retrieve_vlan_ports()
        trunkports = self._find_trunkports(egress, untagged)
        self._logger.debug("trunkports: %r", trunkports)

        self._store_trunkports(trunkports)

    @inlineCallbacks
    def _retrieve_vlan_ports(self):
        query = self.qbridgemib
        egress = yield query.get_vlan_current_egress_ports()
        untagged = yield query.get_vlan_current_untagged_ports()

        if not egress and not untagged:
            egress = yield query.get_vlan_static_egress_ports()
            untagged = yield query.get_vlan_static_untagged_ports()

        return (egress, untagged)

    def _find_trunkports(self, egress, untagged):
        trunkports = defaultdict(list)
        for vlan, (egress, untagged) in mergedicts(egress, untagged).items():
            try:
                tagged = egress - untagged
            except ValueError:
                self._logger.error(
                    "vlan %s subtraction mismatch between "
                    "EgressPorts and UntaggedPorts",
                    vlan,
                )
            else:
                for port in tagged:
                    trunkports[port].append(vlan)
            finally:
                self._logger.debug(
                    "vlan: %s egress: %r untagged: %r", vlan, egress, untagged
                )

        return trunkports

    def _store_trunkports(self, trunkports):
        for port, vlans in trunkports.items():
            self._set_trunkport(port, vlans)

    def _set_trunkport(self, port, vlans):
        if port not in self.baseports:
            self._logger.debug("saw reference to non-existant baseport %s", port)
            return

        # Mark as trunk
        ifindex = self.baseports[port]
        interface = self.containers.factory(ifindex, shadows.Interface)
        interface.trunk = True

        # Store a hex string representation of enabled VLANs
        # in swportallowedvlan
        allowed = self.containers.factory(ifindex, shadows.SwPortAllowedVlan)
        allowed.interface = interface
        allowed.hex_string = vlan_list_to_hex(vlans)

    @inlineCallbacks
    def _get_vlan_names(self):
        names = yield self.qbridgemib.get_vlan_static_names()
        if names:
            for vlannum, name in names.items():
                vlannum = self._remap_vlan(vlannum)
                suffix = '+{}'.format(vlannum)
                name = name.removesuffix(suffix)
                vlan = self.containers.factory(name, shadows.Vlan)
                vlan.net_type = shadows.NetType.get('lan')
                vlan.vlan = vlannum
                vlan.net_ident = name
                vlan.netbox = self.netbox
                self._logger.debug("Found vlan {}: {}".format(vlannum, name))


def vlan_list_to_hex(vlans):
    """Convert a list of VLAN numbers to a hexadecimal string."""
    return SwPortAllowedVlan.vlan_list_to_hex(vlans)

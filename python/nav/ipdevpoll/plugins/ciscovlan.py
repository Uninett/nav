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
"""ipdevpoll plugin to collect 802.1q VLAN information from Cisco devices.

CISCO-VTP-MIB and CISCO-VLAN-MEMBERSHIP-MIB are used as sources for
this plugin.

"""

from twisted.internet import defer

from nav.mibs.if_mib import IfMib
from nav.mibs.cisco_vtp_mib import CiscoVTPMib
from nav.mibs.cisco_vlan_membership_mib import CiscoVlanMembershipMib
from nav.mibs.cisco_vlan_iftable_relationship_mib import CiscoVlanIftableRelationshipMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.enterprise.ids import VENDOR_ID_CISCOSYSTEMS


class CiscoVlan(Plugin):
    """Collect 802.1q info from CISCO-VTP-MIB and CISCO-VLAN-MEMBERSHIP-MIB."""

    _valid_ifindexes = ()

    @classmethod
    def can_handle(cls, netbox):
        daddy_says_ok = super(CiscoVlan, cls).can_handle(netbox)
        if netbox.type:
            vendor_id = netbox.type.get_enterprise_id()
            if vendor_id != VENDOR_ID_CISCOSYSTEMS:
                return False
        return daddy_says_ok

    @defer.inlineCallbacks
    def handle(self):
        ciscovtp = CiscoVTPMib(self.agent)
        ciscovm = CiscoVlanMembershipMib(self.agent)
        ciscovlanif = CiscoVlanIftableRelationshipMib(self.agent)

        enabled_vlans = yield ciscovtp.get_trunk_enabled_vlans(as_bitvector=True)
        native_vlans = yield ciscovtp.get_trunk_native_vlans()
        vlan_membership = yield ciscovm.get_vlan_membership()
        vlan_ifindex = yield ciscovlanif.get_routed_vlan_ifindexes()

        if vlan_membership or native_vlans or enabled_vlans or vlan_ifindex:
            self._logger.debug("vlan_membership: %r", vlan_membership)
            self._logger.debug("native_vlans: %r", native_vlans)
            self._logger.debug("enabled_vlans: %r", enabled_vlans)
            self._logger.debug("vlan_ifindex: %r", vlan_ifindex)

            self._valid_ifindexes = yield self._get_ifindexes()
            self._store_access_ports(vlan_membership)
            self._store_trunk_ports(native_vlans, enabled_vlans)
            self._store_vlan_ifc_relationships(vlan_ifindex)

    @defer.inlineCallbacks
    def _get_ifindexes(self):
        ifmib = IfMib(self.agent)
        indexes = yield ifmib.get_ifindexes()
        return set(indexes)

    def _store_access_ports(self, vlan_membership):
        """Store vlan memberships for all ports."""
        for ifindex, vlan in vlan_membership.items():
            if ifindex not in self._valid_ifindexes:
                self._logger.debug("ignoring info for invalid ifindex %s", ifindex)
                continue

            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.trunk = False
            interface.vlan = vlan
            if not interface.baseport:
                interface.baseport = -ifindex

    def _store_trunk_ports(self, native_vlans, enabled_vlans):
        """Store the set of enabled vlans for each trunk port."""
        for ifindex, vector in enabled_vlans.items():
            if ifindex not in self._valid_ifindexes:
                self._logger.debug("ignoring info for invalid ifindex %s", ifindex)
                continue

            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.trunk = True
            if ifindex in native_vlans:
                interface.vlan = native_vlans[ifindex]

            self._logger.debug(
                "Trunk port %r enabled VLAN count: %s",
                interface.ifname,
                len(vector.get_set_bits()),
            )

            allowed = self.containers.factory(ifindex, shadows.SwPortAllowedVlan)
            allowed.interface = interface
            allowed.hex_string = vector.to_hex()

    def _store_vlan_ifc_relationships(self, routed_vlans):
        for route in routed_vlans:
            ifc = self.containers.factory(route.virtual, shadows.Interface)
            ifc.vlan = route.vlan
            vlan = self.containers.factory(route.virtual, shadows.Vlan)
            vlan.vlan = route.vlan
            if route.physical:
                phys_ifc = self.containers.factory(route.physical, shadows.Interface)
                phys_ifc.trunk = True

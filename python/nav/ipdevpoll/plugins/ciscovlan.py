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
"""ipdevpoll plugin to collect 802.1q VLAN information from Cisco devices.

CISCO-VTP-MIB and CISCO-VLAN-MEMBERSHIP-MIB are used as sources for
this plugin.

"""

from twisted.internet import defer

from nav.mibs.cisco_vtp_mib import CiscoVTPMib
from nav.mibs.cisco_vlan_membership_mib import CiscoVlanMembershipMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows


class CiscoVlan(Plugin):
    """Collect 802.1q info from CISCO-VTP-MIB and CISCO-VLAN-MEMBERSHIP-MIB."""

    @classmethod
    def can_handle(cls, netbox):
        """This plugin handles netboxes"""
        return True

    @defer.inlineCallbacks
    def handle(self):
        """Plugin entrypoint"""

        self._logger.debug("Collecting Cisco-proprietary 802.1q VLAN information")

        self.ciscovtp = CiscoVTPMib(self.agent)
        self.ciscovm = CiscoVlanMembershipMib(self.agent)

        enabled_vlans = yield self.ciscovtp.get_trunk_enabled_vlans(
            as_bitvector=True)
        native_vlans = yield self.ciscovtp.get_trunk_native_vlans()
        vlan_membership = yield self.ciscovm.get_vlan_membership()

        self._store_access_ports(vlan_membership)
        self._store_trunk_ports(native_vlans, enabled_vlans)


    def _store_access_ports(self, vlan_membership):
        """Store vlan memberships for all ports."""
        for ifindex, vlan in vlan_membership.items():
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.trunk = False
            interface.vlan = vlan


    def _store_trunk_ports(self, native_vlans, enabled_vlans):
        """Store the set of enabled vlans for each trunk port."""
        for ifindex, vector in enabled_vlans.items():
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.trunk = True
            if ifindex in native_vlans:
                interface.vlan = native_vlans[ifindex]

            self._logger.debug("Trunk port %r enabled VLAN count: %s",
                              interface.ifname,
                              len(vector.get_set_bits()))

            allowed = self.containers.factory(ifindex,
                                              shadows.SwPortAllowedVlan)
            allowed.interface = interface
            allowed.hex_string = vector.to_hex()

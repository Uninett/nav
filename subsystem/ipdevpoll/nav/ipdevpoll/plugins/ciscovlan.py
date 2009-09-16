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
"""ipdevpoll plugin to collect 802.1q VLAN information from Cisco devices.

CISCO-VTP-MIB and CISCO-VLAN-MEMBERSHIP-MIB are used as sources for
this plugin.

"""

import re

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.mibs import reduce_index
from nav.mibs.cisco_vtp_mib import CiscoVTPMib
from nav.mibs.cisco_vlan_membership_mib import CiscoVlanMembershipMib
from nav.bitvector import BitVector

from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage
from nav.models.manage import Interface


class CiscoVlan(Plugin):
    """Collect 802.1q info from CISCO-VTP-MIB and CISCO-VLAN-MEMBERSHIP-MIB."""

    @classmethod
    def can_handle(cls, netbox):
        """This plugin handles netboxes"""
        return True

    @defer.deferredGenerator
    def handle(self):
        """Plugin entrypoint"""

        self.logger.debug("Collecting Cisco-proprietary 802.1q VLAN information")

        self.ciscovtp = CiscoVTPMib(self.job_handler.agent)
        self.ciscovm = CiscoVlanMembershipMib(self.job_handler.agent)

        dw = defer.waitForDeferred(
            self.ciscovtp.get_trunk_enabled_vlans(as_bitvector=True))
        yield dw
        enabled_vlans = dw.getResult()

        dw = defer.waitForDeferred(self.ciscovtp.get_trunk_native_vlans())
        yield dw
        native_vlans = dw.getResult()

        dw = defer.waitForDeferred(self.ciscovm.get_vlan_membership())
        yield dw
        vlan_membership = dw.getResult()


        self._store_access_ports(vlan_membership)
        self._store_trunk_ports(native_vlans, enabled_vlans)


    def _store_access_ports(self, vlan_membership):
        """Store vlan memberships for all ports."""
        for ifindex, vlan in vlan_membership.items():
            interface = self.job_handler.container_factory(storage.Interface,
                                                           key=ifindex)
            interface.trunk = False
            interface.vlan = vlan


    def _store_trunk_ports(self, native_vlans, enabled_vlans):
        """Store the set of enabled vlans for each trunk port."""
        for ifindex, vector in enabled_vlans.items():
            interface = self.job_handler.container_factory(storage.Interface,
                                                           key=ifindex)
            interface.trunk = True
            if ifindex in native_vlans:
                interface.vlan = native_vlans[ifindex]

            self.logger.debug("Trunk port %r enabled VLAN count: %s",
                              interface.ifname or trunk, 
                              len(vector.get_set_bits()))

            allowed = self.job_handler.container_factory(
                storage.SwPortAllowedVlan, key=ifindex)
            allowed.interface = interface
            allowed.hex_string = vector.to_hex()

#
# Copyright (C) 2011,2012 Uninett AS
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
"""Collects 802.1q VLAN information from Extreme Networks devices.

Uses information from EXTREME-VLAN-MIB and BRIDGE-MIB.

"""

from twisted.internet.defer import inlineCallbacks

from nav.enterprise.ids import VENDOR_ID_EXTREME_NETWORKS
from nav.mibs.extreme_vlan_mib import ExtremeVlanMib
from nav.mibs.bridge_mib import BridgeMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

from .dot1q import vlan_list_to_hex


class ExtremeVlan(Plugin):
    """Collects 802.1q info from EXTREME-VLAN-MIB and BRIDGE-MIB"""

    def __init__(self, *args, **kwargs):
        super(ExtremeVlan, self).__init__(*args, **kwargs)
        self.extremevlan = ExtremeVlanMib(self.agent)
        self.bridge = BridgeMib(self.agent)
        self.baseport_ifindex = {}

    @classmethod
    def can_handle(cls, netbox):
        daddy_says_ok = super(ExtremeVlan, cls).can_handle(netbox)
        if netbox.type:
            vendor_id = netbox.type.get_enterprise_id()
            if vendor_id != VENDOR_ID_EXTREME_NETWORKS:
                return False
        return daddy_says_ok

    def handle(self):
        self._logger.debug(
            "Collecting Extreme Networks proprietary 802.1q VLAN information"
        )
        return self._get_vlan_data()

    @inlineCallbacks
    def _get_vlan_data(self):
        vlan_ports = yield self.extremevlan.get_vlan_ports()
        if not vlan_ports:
            # Doesn't appear to have VLAN data in EXTREME MIBs, get out now.
            return None
        ifindex_vlan = yield self.extremevlan.get_ifindex_vlan_map()
        self.baseport_ifindex = yield self.bridge.get_baseport_ifindex_map()

        vlan_config = self._consolidate_vlan_config(vlan_ports, ifindex_vlan)

        self._store_access_ports(vlan_config)
        self._store_trunk_ports(vlan_config)

    def _consolidate_vlan_config(self, vlan_ports, ifindex_vlan):
        config = {}
        for vlan_ifindex, (tagged, untagged) in vlan_ports.items():
            vlanid = ifindex_vlan.get(vlan_ifindex, None)
            if not vlanid:
                continue
            tagged_indexes = self._portnums_to_ifindexes(tagged)
            untagged_indexes = self._portnums_to_ifindexes(untagged)
            config[vlanid] = (tagged_indexes, untagged_indexes)

        return config

    def _portnums_to_ifindexes(self, portnums):
        return [
            self.baseport_ifindex[portnum]
            for portnum in portnums
            if portnum in self.baseport_ifindex
        ]

    def _store_access_ports(self, vlan_config):
        """Store vlan memberships for all ports."""
        for vlanid, (_tagged, untagged) in vlan_config.items():
            for ifindex in untagged:
                interface = self.containers.factory(ifindex, shadows.Interface)
                interface.trunk = False
                interface.vlan = vlanid

    def _store_trunk_ports(self, vlan_config):
        """Store the set of enabled vlans for each trunk port."""
        ifindex_vlans = {}
        for vlanid, (tagged, _untagged) in vlan_config.items():
            for ifindex in tagged:
                if ifindex not in ifindex_vlans:
                    ifindex_vlans[ifindex] = set()
                ifindex_vlans[ifindex].add(vlanid)

        for ifindex, vlans in ifindex_vlans.items():
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.trunk = True
            interface.vlan = None

            allowed = self.containers.factory(ifindex, shadows.SwPortAllowedVlan)
            allowed.interface = interface
            allowed.hex_string = vlan_list_to_hex(vlans)

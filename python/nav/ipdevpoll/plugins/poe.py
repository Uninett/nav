#
# Copyright (C) 2017 Uninett AS
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
"""Collects power over ethernet information"""
from collections import defaultdict
from twisted.internet.defer import inlineCallbacks, returnValue

from nav.mibs.power_ethernet_mib import PowerEthernetMib
from nav.mibs.cisco_power_ethernet_ext_mib import CiscoPowerEthernetExtMib
from nav.mibs.entity_mib import EntityMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

SNMP_TRUTH_VALUES = {1: True, 2: False}


class Poe(Plugin):
    """Monitors power over ethernet status"""
    def __init__(self, *args, **kwargs):
        super(Poe, self).__init__(*args, **kwargs)
        self.invalid_groups = defaultdict(list)

    @inlineCallbacks
    def handle(self):
        if self.netbox.master:
            self._logger.debug("this is a virtual instance of %s, not polling",
                               self.netbox.master)
            returnValue(None)

        poemib = PowerEthernetMib(self.agent)
        if self.netbox.type and self.netbox.type.vendor.id == 'cisco':
            cisco_mib = CiscoPowerEthernetExtMib(self.agent)
            port_phy_index = yield cisco_mib.retrieve_column(
                "cpeExtPsePortEntPhyIndex")
            group_phy_index = yield cisco_mib.retrieve_column(
                "cpeExtMainPseEntPhyIndex")
            entity_mib = EntityMib(self.agent)
            alias_mapping = yield entity_mib.get_alias_mapping()
            port_ifindices = self._resolve_ifindex(port_phy_index, alias_mapping)
        else:
            port_ifindices = {}
            group_phy_index = {}

        groups = yield poemib.get_groups_table()
        self._process_groups(groups, group_phy_index)

        ports = yield poemib.get_ports_table()
        self._process_ports(ports, port_ifindices)
        self._log_invalid_portgroups()

    def _process_groups(self, groups, phy_indices):
        netbox = self.containers.factory(None, shadows.Netbox)
        for index, row in groups.items():
            self._update_group(netbox, index, row, phy_indices.get(index))

    def _update_group(self, netbox, index, row, phy_index):
        index = index[0]
        group = self.containers.factory(index, shadows.POEGroup)
        group.netbox = self.netbox
        group.index = index
        group.status = row['pethMainPseOperStatus']
        group.power = row['pethMainPsePower']
        group.phy_index = phy_index

    def _process_ports(self, ports, ifindices):
        netbox = self.containers.factory(None, shadows.Netbox)
        for index, row in ports.items():
            self._update_port(netbox, index, row, ifindices.get(index))

    def _update_port(self, netbox, index, row, ifindex):
        grpindex, portindex = index
        poegroup = self.containers.get(grpindex, shadows.POEGroup)
        if not poegroup:
            self.invalid_groups[grpindex].append(portindex)
            return
        port = self.containers.factory((grpindex, portindex), shadows.POEPort)
        port.netbox = self.netbox
        port.index = portindex
        port.poegroup = poegroup
        port.admin_enable = SNMP_TRUTH_VALUES.get(row['pethPsePortAdminEnable'], False)
        port.detection_status = row['pethPsePortDetectionStatus']
        port.priority = row['pethPsePortPowerPriority']
        port.classification = row['pethPsePortPowerClassifications']
        vendor = self.netbox.type.vendor.id if self.netbox.type else ''
        if not ifindex and vendor == 'hp':
            ifindex = portindex
        if ifindex:
            port.interface = self.containers.factory(ifindex,
                                                     shadows.Interface)
            port.interface.netbox = netbox
            port.interface.ifindex = ifindex

    def _resolve_ifindex(self, phy_indices, alias_mapping):
        result = {}
        for portindex, phy_index in phy_indices.items():
            if phy_index in alias_mapping:
                ifindices = alias_mapping[phy_index]
                if len(ifindices) != 1:
                    self._logger.warning(
                        "Found unexpected number of ifindices for phy_index %s",
                        phy_index)
                    continue
                result[portindex] = ifindices[0]
        return result

    def _log_invalid_portgroups(self):
        if not self.invalid_groups:
            return

        valid_groups = (list(self.containers[shadows.POEGroup].keys())
                        if shadows.POEGroup in self.containers else [])

        for group in self.invalid_groups:
            self.invalid_groups[group].sort()
            self._logger.info(
                "ignoring PoE ports in invalid PoE groups: group=%s ports=%s",
                group, self.invalid_groups[group])
        self._logger.info("Valid PoE groups for this device are: %s",
                          valid_groups)

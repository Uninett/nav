#
# Copyright (C) 2017 UNINETT AS
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
"""Collects power over ethernet information"""
from twisted.internet.defer import inlineCallbacks, returnValue

from nav.mibs.power_ethernet_mib import PowerEthernetMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows


class poe(Plugin):
    """Monitors power over ethernet status"""

    @inlineCallbacks
    def handle(self):
        if self.netbox.master:
            self._logger.debug("this is a virtual instance of %s, not polling",
                               self.netbox.master)
            returnValue(None)

        poemib = PowerEthernetMib(self.agent)

        groups = yield poemib.get_groups_table()
        self._process_groups(groups)

        ports = yield poemib.get_ports_table()
        self._process_ports(ports)

    def _process_groups(self, groups):
        netbox = self.containers.factory(None, shadows.Netbox)
        for index, row in groups.items():
            self._update_group(netbox, index, row)

    def _update_group(self, netbox, index, row):
        index = index[0]
        group = self.containers.factory(index, shadows.POEGroup)
        group.netbox = self.netbox
        group.index = index
        group.status = row['pethMainPseOperStatus']
        group.power = row['pethMainPsePower']

    def _process_ports(self, ports):
        netbox = self.containers.factory(None, shadows.Netbox)
        for index, row in ports.items():
            self._update_port(netbox, index, row)

    def _update_port(self, netbox, index, row):
        grpindex, portindex = index
        port = self.containers.factory((grpindex, portindex), shadows.POEPort)
        port.netbox = self.netbox
        port.index = portindex
        port.poegroup = self.containers.factory(grpindex, shadows.POEGroup)
        port.admin_enable = row['pethPsePortAdminEnable']
        port.detection_status = row['pethPsePortDetectionStatus']
        port.priority = row['pethPsePortPowerPriority']
        port.classification = row['pethPsePortPowerClassifications']

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
"""ipdevpoll plugin to collect bridge data.

This plugin doesn't do much except find baseport numbers for switch
ports, using the BRIDGE-MIB.  The plugin also supports multiple
BRIDGE-MIB instances if they are listed as logical entities in
ENTITY-MIB. The plugin also fetches the base bridge address from the bridge mib

"""

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.utils import get_multibridgemib, binary_mac_to_hex

INFO_KEY_BRIDGE_INFO = 'bridge_info'
INFO_VAR_BASE_ADDRESS = 'base_address'


class Bridge(Plugin):
    "Finds interfaces in L2/switchport mode"

    @defer.inlineCallbacks
    def handle(self):
        bridge = yield get_multibridgemib(self.agent)
        bridge_address = yield bridge.get_base_bridge_address()
        if bridge_address:
            self._save_bridge_address(bridge_address)
        baseports = yield bridge.get_baseport_ifindex_map()
        return self._set_port_numbers(baseports)

    def _save_bridge_address(self, bridge_address):
        info = self.containers.factory(
            (INFO_KEY_BRIDGE_INFO, INFO_VAR_BASE_ADDRESS), shadows.NetboxInfo
        )
        info.value = binary_mac_to_hex(bridge_address)
        info.netbox = self.netbox
        info.key = INFO_KEY_BRIDGE_INFO
        info.variable = INFO_VAR_BASE_ADDRESS

    def _set_port_numbers(self, baseports):
        "Processes a dictionary of {portnumber: ifindex} mappings"

        self._logger.debug(
            "Found %d base (switch) ports: %r", len(baseports), baseports
        )

        for portnum, ifindex in baseports.items():
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.ifindex = ifindex
            interface.baseport = portnum

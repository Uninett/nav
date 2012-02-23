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
"""ipdevpoll plugin to collect bridge data.

This plugin doesn't do much except find baseport numbers for switch
ports, using the BRIDGE-MIB.  The plugin also supports multiple
BRIDGE-MIB instances if they are listed as logical entities in
ENTITY-MIB.

"""
from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.utils import get_multibridgemib

class Bridge(Plugin):
    "Finds interfaces in L2/switchport mode"

    @defer.inlineCallbacks
    def handle(self):
        bridge = yield get_multibridgemib(self.agent)
        baseports = yield bridge.get_baseport_ifindex_map()
        defer.returnValue(self._set_port_numbers(baseports))

    def _set_port_numbers(self, baseports):
        "Processes a dictionary of {portnumber: ifindex} mappings"

        self._logger.debug("Found %d base (switch) ports: %r",
                           len(baseports), baseports)

        for portnum, ifindex in baseports.items():
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.ifindex = ifindex
            interface.baseport = portnum

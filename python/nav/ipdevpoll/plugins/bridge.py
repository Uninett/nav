#
# Copyright (C) 2009-2012 UNINETT AS
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
"ipdevpoll plugin to collect bridge data"

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.utils import get_multibridgemib
from nav.mibs import reduce_index
from nav.mibs.cisco_vtp_mib import CiscoVTPMib

VENDORID_CISCO = 9

class Bridge(Plugin):
    """This plugin will just figure out which interfaces on a device are
    switch ports, normally found via the BRIDGE-MIB::dot1dBasePortTable. The
    data model identifies switch ports by setting a base port number in
    Interface.baseport.

    Cisco switches, however, will implement a BRIDGE-MIB instance per
    operational VLAN. Each instance must be accessed individually using a VLAN
    indexed SNMP community. This is effing inefficient when we want to get
    inventory information as quickly as possible, so for Cisco we instead will
    look at which interfaces are listed in the proprietary
    CISCO-VTP-MIB::vlanTrunkPortTable. Baseport numbers will be set equal to
    ifindexes in this case, but the value of these numbers have no
    significance in NAV.

    """
    @defer.inlineCallbacks
    def handle(self):
        vendor_id = (self.netbox.type.get_enterprise_id()
                     if self.netbox.type else None)
        if vendor_id == VENDORID_CISCO:
            baseports = yield self._fake_baseports_from_cisco_swports()
        else:
            baseports = {}

        if not baseports:
            bridge = yield get_multibridgemib(self.agent)
            baseports = yield bridge.get_baseport_ifindex_map()

        defer.returnValue(self._set_port_numbers(baseports))

    @defer.inlineCallbacks
    def _fake_baseports_from_cisco_swports(self):
        self._logger.debug("getting list of switch ports from CISCO-VTP-MIB")
        vtp = CiscoVTPMib(self.agent)
        swports = yield vtp.retrieve_column(
            'vlanTrunkPortDynamicStatus').addCallback(reduce_index)
        baseports = dict((ifindex, ifindex) for ifindex in swports)
        defer.returnValue(baseports)

    def _set_port_numbers(self, baseports):
        "Processes a dictionary of {portnumber: ifindex} mappings"

        self._logger.debug("Found %d base (switch) ports: %r",
                           len(baseports), baseports)

        for portnum, ifindex in baseports.items():
            interface = self.containers.factory(ifindex, shadows.Interface)
            interface.ifindex = ifindex
            interface.baseport = portnum

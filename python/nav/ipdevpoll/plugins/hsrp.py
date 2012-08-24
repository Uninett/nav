#
# Copyright (C) 2012 UNINETT AS
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
"""ipdevpoll plugin to poll Cisco HSRP address information"""
from IPy import IP
from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll.shadows import GwPortPrefix
from nav.mibs.cisco_hsrp_mib import CiscoHSRPMib

VENDORID_CISCO = 9

class HSRP(Plugin):
    """ipdevpoll plugin to collect HSRP addresses.

    This will only update addresses collected already by a plugin that ran
    before on the same ContainerRepository.

    """

    @classmethod
    def can_handle(cls, netbox):
        daddy_says_ok = super(HSRP, cls).can_handle(netbox)
        if netbox.type:
            vendor_id = netbox.type.get_enterprise_id()
            if vendor_id != VENDORID_CISCO:
                return False
        return daddy_says_ok

    def __init__(self, *args, **kwargs):
        super(HSRP, self).__init__(*args, **kwargs)
        self.hsrp = CiscoHSRPMib(self.agent)

    @defer.inlineCallbacks
    def handle(self):
        """Handles HSRP collection"""
        if self.gwportprefixes_found():
            addresses = yield self.hsrp.get_virtual_addresses()
            self.update_containers_with(addresses)

    def gwportprefixes_found(self):
        if GwPortPrefix not in self.containers:
            self._logger.debug("there are no collected GwPortPrefixes to "
                               "update")
            return False
        else:
            return True

    def update_containers_with(self, addresses):
        if addresses:
            self._logger.debug("Found HSRP addresses: %r", addresses)
        for gwp_prefix in self.containers[GwPortPrefix].values():
            gwp_prefix.hsrp = IP(gwp_prefix.gw_ip) in addresses

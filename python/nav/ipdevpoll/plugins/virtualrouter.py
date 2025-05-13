#
# Copyright (C) 2012 Uninett AS
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
"""ipdevpoll plugin to poll Cisco HSRP address information"""

from IPy import IP
from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll.shadows import GwPortPrefix
from nav.mibs.vrrp_mib import VRRPMib
from nav.mibs.cisco_hsrp_mib import CiscoHSRPMib


class VirtualRouter(Plugin):
    """ipdevpoll plugin to collect Virtual Router addresses from VRRP and
    HSRP routers.

    These addresses are marked as virtual in NAV database,
    and will ensure that networks with redundant routers aren't classified
    incorrectly as link networks.

    This plugin will only update existing addresses that were collected by a
    plugin that ran before this one in the same job (such as the Prefix
    plugin). This is to ensure we don't create addresses that aren't active
    on the router.

    """

    @classmethod
    def can_handle(cls, netbox):
        daddy_says_ok = super(VirtualRouter, cls).can_handle(netbox)
        return daddy_says_ok and netbox.category.id in ('GW', 'GSW')

    def __init__(self, *args, **kwargs):
        super(VirtualRouter, self).__init__(*args, **kwargs)
        self.mibs = [mib(self.agent) for mib in (CiscoHSRPMib, VRRPMib)]

    @defer.inlineCallbacks
    def handle(self):
        """Handles address collection"""
        if self.gwportprefixes_found():
            mibs = []
            virtual_addrs = set()

            for mib in self.mibs:
                addrs_from_mib = yield mib.get_virtual_addresses()
                virtual_addrs.update(addrs_from_mib)
                if addrs_from_mib:
                    mibs.append(mib.mib['moduleName'])

            self.update_containers_with(virtual_addrs, mibs)

    def gwportprefixes_found(self):
        if GwPortPrefix not in self.containers:
            self._logger.debug("there are no collected GwPortPrefixes to update")
            return False
        else:
            return True

    def update_containers_with(self, addresses, from_mib=None):
        if addresses:
            self._logger.debug(
                "Found virtual addresses from %s: %r", from_mib, addresses
            )
        for gwp_prefix in self.containers[GwPortPrefix].values():
            gwp_prefix.virtual = IP(gwp_prefix.gw_ip) in addresses

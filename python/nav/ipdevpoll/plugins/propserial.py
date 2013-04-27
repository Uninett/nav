#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""retrieves chassis serial numbers from various proprietary MIBs"""

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll.shadows import Netbox, Device

from nav.mibs.juniper_mib import JuniperMib
from nav.mibs.powernet_mib import PowerNetMib

VENDORID_APC = 318
VENDORID_JUNIPER = 2636

VENDOR_MIBS = {
    VENDORID_APC: PowerNetMib,
    VENDORID_JUNIPER: JuniperMib,
}


class ProprietarySerial(Plugin):
    """retrieves chassis serial numbers from various proprietary MIBs"""
    RESTRICT_TO_VENDORS = [VENDORID_APC, VENDORID_JUNIPER]

    @defer.inlineCallbacks
    def handle(self):
        vendor_id = self.netbox.type.get_enterprise_id()
        mibclass = VENDOR_MIBS.get(vendor_id, None)
        if mibclass:
            mib = mibclass(self.agent)
            serial = yield mib.get_serial_number()
            if serial:
                self._logger.debug("got a chassis serial number from %s: %r",
                                   mib.mib.get('moduleName', None), serial)
                self._set_chassis_serial(serial)


    def _set_chassis_serial(self, serial):
        netbox = self.containers.factory(None, Netbox)
        if not netbox.device:
            if not self.containers.get(None, Device):
                netbox.device = self.containers.factory(None, Device)
                self.containers[Device][serial] = netbox.device
            else:
                netbox.device = self.containers.get(None, Device)

        netbox.device.serial = serial

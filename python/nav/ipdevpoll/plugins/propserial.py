#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
from nav.ipdevpoll.shadows import Netbox, Device, NetboxEntity
from nav.models import manage

from nav.mibs.hp_httpmanageable_mib import HPHTTPManageableMib
from nav.mibs.juniper_mib import JuniperMib
from nav.mibs.powernet_mib import PowerNetMib
from nav.enterprise.ids import (
    VENDOR_ID_HEWLETT_PACKARD,
    VENDOR_ID_AMERICAN_POWER_CONVERSION_CORP,
    VENDOR_ID_JUNIPER_NETWORKS_INC,
)


VENDOR_MIBS = {
    VENDOR_ID_HEWLETT_PACKARD: HPHTTPManageableMib,
    VENDOR_ID_AMERICAN_POWER_CONVERSION_CORP: PowerNetMib,
    VENDOR_ID_JUNIPER_NETWORKS_INC: JuniperMib,
}


class ProprietarySerial(Plugin):
    """retrieves chassis serial numbers from various proprietary MIBs"""

    RESTRICT_TO_VENDORS = VENDOR_MIBS.keys()

    @defer.inlineCallbacks
    def handle(self):
        vendor_id = self.netbox.type.get_enterprise_id()
        mibclass = VENDOR_MIBS.get(vendor_id, None)
        if mibclass:
            mib = mibclass(self.agent)
            serial = yield mib.get_serial_number()
            if serial:
                self._logger.debug(
                    "got a chassis serial number from %s: %r",
                    mib.mib.get('moduleName', None),
                    serial,
                )
                self._set_chassis_serial(serial, mib.mib.get('moduleName'))

    def _set_chassis_serial(self, serial, source):
        netbox = self.containers.factory(None, Netbox)
        chassis = NetboxEntity.get_chassis_entities(self.containers)
        if not chassis:
            entity = self.containers.factory(None, NetboxEntity)
            device = self.containers.factory(serial, Device)
            device.serial = serial

            entity.netbox = netbox
            entity.index = 0
            entity.source = source
            entity.physical_class = manage.NetboxEntity.CLASS_CHASSIS
            entity.device = device

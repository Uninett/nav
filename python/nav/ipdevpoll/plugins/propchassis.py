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
"""retrieves chassis details from various proprietary MIBs"""

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll.shadows import Netbox, Device, NetboxEntity
from nav.models import manage

from nav.mibs.hp_httpmanageable_mib import HPHTTPManageableMib
from nav.mibs.juniper_mib import JuniperMib
from nav.mibs.powernet_mib import PowerNetMib
from nav.mibs.pdu2_mib import PDU2Mib
from nav.enterprise.ids import (VENDOR_ID_HEWLETT_PACKARD,
                                VENDOR_ID_RARITAN_COMPUTER_INC,
                                VENDOR_ID_AMERICAN_POWER_CONVERSION_CORP,
                                VENDOR_ID_JUNIPER_NETWORKS_INC)


VENDOR_MIBS = {
    VENDOR_ID_HEWLETT_PACKARD: HPHTTPManageableMib,
    VENDOR_ID_RARITAN_COMPUTER_INC: PDU2Mib,
    VENDOR_ID_AMERICAN_POWER_CONVERSION_CORP: PowerNetMib,
    VENDOR_ID_JUNIPER_NETWORKS_INC: JuniperMib,
}




""" Lookup dict to get what chassis attributes to discover per mode  """

VENDOR_ITEMS_DISCOVERY = {
            VENDOR_ID_HEWLETT_PACKARD: ('serial'),
            VENDOR_ID_RARITAN_COMPUTER_INC: ('serial', 'model_name', 'firmware_revision'),
            VENDOR_ID_AMERICAN_POWER_CONVERSION_CORP: ('serial'),
            VENDOR_ID_JUNIPER_NETWORKS_INC: ('serial'),
}



class ProprietaryChassis(Plugin):
    """retrieves chassis details from various proprietary MIBs"""
    RESTRICT_TO_VENDORS = VENDOR_MIBS.keys()

    @defer.inlineCallbacks
    def handle(self):
        vendor_id = self.netbox.type.get_enterprise_id()
        mibclass = VENDOR_MIBS.get(vendor_id, None)
        discovery_items = VENDOR_ITEMS_DISCOVERY.get(vendor_id, None)
        self._logger.debug(discovery_items)
        if mibclass:
            mib = mibclass(self.agent)

            if 'serial' in discovery_items:
                serial = yield mib.get_serial_number()
                if serial:
                    self._logger.debug("got a chassis serial number from %s: %r",
                                        mib.mib.get('moduleName', None), serial)
                    self._set_chassis_serial(serial, mib.mib.get('moduleName'))

            if 'model_name' in discovery_items:
                ModelName = yield mib.get_model_name()
                if ModelName:
                    self._logger.debug("got a chassis model details from %s: %r",
                                        mib.mib.get('moduleName', None), ModelName)
                    self._set_chassis_model_name(ModelName, mib.mib.get('moduleName'))

            if 'firmware_revision' in discovery_items:
                    fw_ver = yield mib.get_firmware_revision()
                    if fw_ver:
                        self._logger.debug("got a chassis firmware ver from %s: %r",
                                        mib.mib.get('moduleName', None), fw_ver)
                        self._set_chassis_fw_version(fw_ver, mib.mib.get('moduleName'))


    def _set_chassis_model_name(self, ModelName, source):
        """ Check for Chassis Model already created and update model when found"""
        netbox = self.containers.factory(None, Netbox)
        chassis = NetboxEntity.get_chassis_entities(self.containers)
        if chassis and len(chassis) == 1:
            entity = chassis[0]
            self._logger.debug("found a pre-existing chassis: %s/%s (%s)",
                               entity.name, entity.source,
                               entity.device.serial if entity.device else "N/A")

            if ModelName:
               entity.model_name = ModelName
               self._logger.debug("set Chassis Model Name")


        def _set_chassis_fw_version(self, fw_ver, source):
            """ Check for Chassis Model already created and update fw_ver when found"""
            netbox = self.containers.factory(None, Netbox)
            chassis = NetboxEntity.get_chassis_entities(self.containers)
            if chassis and len(chassis) == 1:
                entity = chassis[0]
                self._logger.debug("found a pre-existing chassis: %s/%s (%s)",
                               entity.name, entity.source,
                               entity.device.serial if entity.device else "N/A")

            if fw_ver:
               entity.firmware_revision = fw_ver
               self._logger.debug("set firmware revision ")


    def _set_chassis_serial(self, serial, source):
        """ Due to legacy usages serial is part of Device Model"""
        self._logger.info(self, serial, source)
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

# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 UNINETT AS
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
"""ipdevpoll plugin to collect sensor data.

This plugin use CISCO-ENVMON-MIB, ENTITY-SENSOR-MIB and IT-WATCHDOGS-MIB-V3
to retrieve all possible sensors in network-equipment.
"""


from nav.mibs import reduce_index
from nav.mibs.itw_mibv3 import ItWatchDogsMibV3
from nav.mibs.cisco_envmon_mib import CiscoEnvMonMib
from nav.mibs.entity_sensor_mib import EntitySensorMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.utils import binary_mac_to_hex

VENDOR_CISCO = 9
VENDOR_HP = 11
VENDOR_ITWATCHDOGS = 17373

class MIBFactory(object):
    @classmethod
    def get_instance(self, netbox, agent):
        vendor_id = netbox.type.get_enterprise_id()
        if (vendor_id == VENDOR_CISCO):
            mib = CiscoEnvMonMib(agent)
            return mib
        if (vendor_id == VENDOR_ITWATCHDOGS):
            mib = ItWatchDogsMibV3(agent)
            return mib
        mib = EntitySensorMib(agent)
        return mib
        
class Sensors(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self._logger.error('Sensors: handle')
        self._logger.error('netbox = %s' % self.netbox)
        self.mib = MIBFactory.get_instance(self.netbox, self.agent)
        df = self.mib.get_all_sensors()
        df.addCallback(self._store_sensors)
        return df

    def _store_sensors(self, result):
        sensors = []
        for row in result:
            oid = row.get('oid', None)
            sensor = self.containers.factory(oid,  shadows.Sensor)
            sensor.netbox = self.netbox
            sensor.oid = oid
            sensor.unit_of_measurement = row.get('unit_of_measurement', None)
            sensor.data_scale = row.get('scale', None)
            sensor.human_readable = row.get('description', None)
            sensor.name = row.get('name', None)
            sensor.internal_name = row.get('internal_name', None)
            sensor.mib = row.get('mib', None)
            sensors.append(sensors)
        return sensors

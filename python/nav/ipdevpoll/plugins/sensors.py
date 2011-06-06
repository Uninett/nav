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
        vendor_id = self.netbox.get_enterprise_id()
        if (vendor_id == VENDOR_CISCO):
            mib = CiscoEnvMonMib(agent)
            mib.retrieve_columns([])
            return mib
        if (vendor_id = VENDOR_ITWATCHDOGS):
            mib = ItWatchDogsMibV3(agent)
            mib.retrieve_columns([
                'climateName',
                'climateTempC',
                'climateHumidity',
                'climateLight',
                'climateAirflow',
                'climateSound',
                'climateDewPointC',
                'powMonName',
                'powMonKWattHrs',
                'powMonVolts',
                'powMonDeciAmps',
                'powMonRealPower',
                'powMonApparentPower',
                '',
                'tempSensorName',
                'tempSensorAvail',
                'tempSensorTempC',
                'airFlowSensorName',
                'airFlowSensorAvail',
                'airFlowSensorTempC',
                'airFlowSensorFlow',
                'airFlowSensorHumidity',
                'airFlowSensorDewPointC',
                'powerName',
                'powerAvail',
                'powerVolts',
                'powerDeciAmps',
                'powerRealPower',
                'powerApparentPower',
                'powerPowerFactor',
                'doorSensorName',
                'doorSensorAvail',
                'doorSensorStatus',
                'waterSensorName',
                'waterSensorAvail',
                'waterSensorDampness',
                'currentMonitorName',
                'currentMonitorAvail',
                'currentMonitorDeciAmps',
                'millivoltMonitorName',
                'millivoltMonitorAvail',
                'millivoltMonitorMV',
                ])
            return mib

        mib = EntitySensorMib(agent)
        mib.retrieve_columns([
                'entPhySensorType',
                'entPhySensorScale',
                'entPhySensorPrecision',
                'entPhySensorUnitsDisplay',
                ])
        return mib
        
class Sensors(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self._logger.error('Sensors: handle')
        self._logger.error('netbox = %s' % self.netbox)
        self.mib = MIBFactory.get_instance(self.netbox, self.agent)
        df.addCallback(reduce_index)
        df.addCallback(self._handle_handle)
        return df

    def _handle_handle(self, res):
        self._logger.error('Sensors: _handle_handle')
        return []

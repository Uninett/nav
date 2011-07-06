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


from nav.mibs.itw_mib import ItWatchDogsMib
from nav.mibs.itw_mibv3 import ItWatchDogsMibV3
from nav.mibs.cisco_envmon_mib import CiscoEnvMonMib
from nav.mibs.entity_sensor_mib import EntitySensorMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

VENDOR_CISCO = 9
VENDOR_HP = 11
VENDOR_ITWATCHDOGS = 17373


class MIBFactory(object):
    """A class that produces mibs depending and netbox-vendors
    and -models."""

    @classmethod
    def get_instance(self, netbox, agent):
        """ Factory for allocating mibs based on
        netbox-vendors and -models"""
        vendor_id = netbox.type.get_enterprise_id()
        if vendor_id == VENDOR_CISCO:
            # Some cisco-boxes may use standard-mib
            return [EntitySensorMib(agent), CiscoEnvMonMib(agent)]
        elif vendor_id == VENDOR_ITWATCHDOGS:
            # Try with the most recent first
            return [ItWatchDogsMibV3(agent), ItWatchDogsMib(agent)]
        return [EntitySensorMib(agent)]


class Sensors(Plugin):
    """ Plugin that detect sensors in netboxes."""

    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        """ Collect sensors and feed them in to persistent store."""
        self._logger.debug('Collection sensors data')
        mibs = MIBFactory.get_instance(self.netbox, self.agent)
        for mib in mibs:
            df = mib.get_all_sensors()
            df.addCallback(self._store_sensors)
        return df

    def _store_sensors(self, result):
        """ Store sensor-records to database (this is actually
            done automagically when we use shadow-objects."""
        self._logger.debug('Found %d sensors', len(result))
        sensors = []
        for row in result:
            oid = row.get('oid', None)
            sensor = self.containers.factory(oid, shadows.Sensor)
            sensor.netbox = self.netbox
            sensor.oid = oid
            sensor.unit_of_measurement = row.get('unit_of_measurement', None)
            sensor.precision = row.get('precision', 0)
            sensor.data_scale = row.get('scale', None)
            sensor.human_readable = row.get('description', None)
            sensor.name = row.get('name', None)
            sensor.internal_name = row.get('internal_name', None)
            sensor.mib = row.get('mib', None)
            sensors.append(sensors)
        return sensors

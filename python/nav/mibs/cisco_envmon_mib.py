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
import re

from twisted.internet import defer
from twisted.internet import threads

from nav.mibs import reduce_index

import mibretriever

POWER_SENSOR_TYPE = {
    1: 'Power supply source unknown',
    2: 'AC power supply',
    3: 'DC power supply',
    4: 'External power supply',
    5: 'Internal redundant power supply',
}

class CiscoEnvMonMib(mibretriever.MibRetriever):
    from nav.smidumps.cisco_envmon_mib import MIB as mib

    def get_module_name(self):
        return self.mib.get('moduleName', None)

    @defer.inlineCallbacks
    def can_return_sensors(self):
        temperature_sensors = yield self._get_temperature_sensors()
        if len(temperature_sensors) > 0:
            defer.returnValue(True)
        voltage_sensors = yield self._get_voltage_sensors()
        if len(voltage_sensors) > 0:
            defer.returnValue(True)
        fanstate_sensors = yield self._get_fanstate_sensors()
        if len(fanstate_sensors) > 0:
            defer.returnValue(True)
        powersupply_sensors = yield self._get_powersupply_sensors()
        if len(powersupply_sensors) > 0:
            defer.returnValue(True)
        defer.returnValue(False)

    def _get_voltage_sensors(self):
        df = self.retrieve_columns([
                'ciscoEnvMonVoltageStatusDescr',
                'ciscoEnvMonVoltageStatusValue',
                'ciscoEnvMonVoltageState',
                ])
        df.addCallback(reduce_index)
        return df

    def _get_temperature_sensors(self):
        df = self.retrieve_columns([
                'ciscoEnvMonTemperatureStatusIndex',
                'ciscoEnvMonTemperatureStatusDescr',
                'ciscoEnvMonTemperatureStatusValue',
                'ciscoEnvMonTemperatureState',
                ])
        df.addCallback(reduce_index)
        return df

    def _get_fanstate_sensors(self):
        df = self.retrieve_columns([
                'ciscoEnvMonFanStatusIndex',
                'ciscoEnvMonFanStatusDescr',
                'ciscoEnvMonFanState',
                ])
        df.addCallback(reduce_index)
        return df

    def _get_powersupply_sensors(self):
        df = self.retrieve_columns([
                'ciscoEnvMonSupplyStatusIndex',
                'ciscoEnvMonSupplyStatusDescr',
                'ciscoEnvMonSupplyState',
                'ciscoEnvMonSupplySource',
                ])
        df.addCallback(reduce_index)
        return df

    def _get_voltage_sensor_params(self, voltage_sensors):
        sensors = []
        for idx, voltage_sensor in voltage_sensors.items():
            voltage_sensor_oid = voltage_sensor.get(0, None)
            voltage_mib = self.nodes.get('ciscoEnvMonVoltageStatusValue', None)
            oid = str(voltage_mib.oid) + str(voltage_sensor_oid)
            unit_of_measurement = 'Volts'
            precision = 0
            scale = self.mib.get('nodes').get(
                    'ciscoEnvMonVoltageStatusValue').get(
                    'units').strip().capitalize()
            scale = re.sub('volts$', '', scale)
            description = voltage_sensor.get(
                    'ciscoEnvMonVoltageStatusDescr').strip()
            name = description
            internal_name = description
            sensors.append({
                            'oid': oid,
                            'unit_of_measurement' : unit_of_measurement,
                            'precision': precision,
                            'scale': scale,
                            'description': description,
                            'name': name,
                            'internal_name': internal_name,
                            'mib': self.get_module_name(),
                            })
        return sensors

    def _get_temperature_sensor_params(self, temperature_sensors):
        sensors = []
        for idx, temp_sensor in temperature_sensors.items():
            temp_sensor_oid = temp_sensor.get(0, None)
            temp_mib = self.nodes.get('ciscoEnvMonTemperatureStatusValue', None)
            oid = str(temp_mib.oid) + str(temp_sensor_oid)
            unit_of_measurement = self.mib.get('nodes').get(
                    'ciscoEnvMonTemperatureStatusValue').get(
                    'units').strip().capitalize()
            precision = 0
            scale = None
            description = temp_sensor.get(
                    'ciscoEnvMonTemperatureStatusDescr').strip()
            name = description
            internal_name = description
            sensors.append({
                            'oid': oid,
                            'unit_of_measurement' : unit_of_measurement,
                            'precision': precision,
                            'scale': scale,
                            'description': description,
                            'name': name,
                            'internal_name': internal_name,
                            'mib': self.get_module_name(),
                            })
        return sensors

    def _get_fanstate_sensor_params(self, fanstate_sensors):
        sensors = []
        for idx, fanstate_sensor in fanstate_sensors.items():
            fanstate_sensor_oid = fanstate_sensor.get(0, None)
            fanstate_mib = self.nodes.get('ciscoEnvMonFanState', None)
            oid = str(fanstate_mib.oid) + str(fanstate_sensor_oid)
            unit_of_measurement = 'Fan state'
            precision = 0
            scale = None
            description = fanstate_sensor.get(
                    'ciscoEnvMonFanStatusDescr').strip()
            name = description
            internal_name = description
            sensors.append({
                            'oid': oid,
                            'unit_of_measurement' : unit_of_measurement,
                            'precision' : precision,
                            'scale': scale,
                            'description': description,
                            'name': name,
                            'internal_name': internal_name,
                            'mib': self.get_module_name(),
                            })
        return sensors

    def _get_powersupply_sensor_params(self, powersupply_sensors):
        sensors = []
        for idx, power_sensor in powersupply_sensors.items():
            power_sensor_oid = power_sensor.get(0, None)
            power_mib = self.nodes.get('ciscoEnvMonSupplyState', None)
            oid = str(power_mib.oid) + str(power_sensor_oid)
            unit_of_measurement = 'Power supply state'
            precision = 0
            scale = None
            power_source = power_sensor.get('ciscoEnvMonSupplySource', None)
            description = POWER_SENSOR_TYPE.get(power_source)
            name = power_sensor.get('ciscoEnvMonSupplyStatusDescr').strip()
            # Sometimes we do get a source
            if not description:
                description = name
            internal_name = name
            sensors.append({
                            'oid': oid,
                            'unit_of_measurement' : unit_of_measurement,
                            'precision': precision,
                            'scale': scale,
                            'description': description,
                            'name': name,
                            'internal_name': internal_name,
                            'mib': self.get_module_name(),
                            })
        return sensors

    @defer.inlineCallbacks
    def get_all_sensors(self):
        voltage_sensors = yield self._get_voltage_sensors()
        temperature_sensors = yield self._get_temperature_sensors()
        fanstate_sensors = yield self._get_fanstate_sensors()
        powersupply_sensors = yield self._get_powersupply_sensors()

        result = self._get_voltage_sensor_params(voltage_sensors)
        result.extend(self._get_temperature_sensor_params(temperature_sensors))
        result.extend(self._get_fanstate_sensor_params(fanstate_sensors))
        result.extend(self._get_powersupply_sensor_params(powersupply_sensors))

        self.logger.debug('get_all_sensors: result=%s' % result)   
        defer.returnValue(result)

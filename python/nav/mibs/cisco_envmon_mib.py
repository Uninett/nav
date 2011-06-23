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

    def retrieve_std_columns(self):
        """ A convenient function for getting the most interesting
        columns for environment mibs. """
        return self.retrieve_columns([
                'ciscoEnvMonVoltageStatusDescr',
                'ciscoEnvMonVoltageStatusValue',
                'ciscoEnvMonVoltageThresholdLow',
                'ciscoEnvMonVoltageThresholdHigh',
                'ciscoEnvMonVoltageLastShutdown',
                'ciscoEnvMonVoltageState',
                'ciscoEnvMonTemperatureStatusIndex',
                'ciscoEnvMonTemperatureStatusDescr',
                'ciscoEnvMonTemperatureStatusValue',
                'ciscoEnvMonTemperatureThreshold',
                'ciscoEnvMonTemperatureLastShutdown',
                'ciscoEnvMonTemperatureState',
                'ciscoEnvMonFanStatusIndex',
                'ciscoEnvMonFanStatusDescr',
                'ciscoEnvMonFanState',
                'ciscoEnvMonSupplyStatusIndex',
                'ciscoEnvMonSupplyStatusDescr',
                'ciscoEnvMonSupplyState',
                'ciscoEnvMonSupplySource',
                ])

    def get_module_name(self):
        return self.mib.get('moduleName', None)

    def _get_power_sensor_descriptions(self, row):
        row_oid = row.get(0, None)
        mib_object = self.nodes.get('ciscoEnvMonSupplyState', None)
        oid = str(mib_object.oid) + str(row_oid)
        # measurement is to check if power-supply is available
        power_supply_source = row.get('ciscoEnvMonSupplySource', None)
        unit_of_measurement =  POWER_SENSOR_TYPE.get(power_supply_source, None)
        scale = None
        description = row.get('ciscoEnvMonSupplyStatusDescr', None)
        if description:
            description.strip().capitalize()
        return { 'oid': oid,
                 'unit_of_measurement': unit_of_measurement,
                 'scale': scale,
                 'description': description,
               }

    def _get_fan_sensor_descriptions(self, row):
        row_oid = row.get(0, None)
        mib_object = self.nodes.get('ciscoEnvMonFanState', None)
        oid = str(mib_object.oid) + str(row_oid)
        unit_of_measurement = 'Fan state'
        scale = None
        description = row.get('ciscoEnvMonFanStatusDescr', None)
        if description:
             description.strip().capitalize()
        return { 'oid': oid,
                 'unit_of_measurement': unit_of_measurement,
                 'scale': scale,
                 'description': description,
               }

    def _get_temp_sensor_descriptions(self, row):
        row_oid = row.get(0, None)
        mib_object = self.nodes.get('ciscoEnvMonTemperatureStatusValue', None)
        oid = str(mib_object.oid) + str(row_oid)
        unit_of_measurement = self.mib.get('nodes').get(
                    'ciscoEnvMonTemperatureStatusValue').get(
                        'units').strip().capitalize()
        scale = None
        description = row.get('ciscoEnvMonTemperatureStatusDescr', None)
        if description:
            description.strip().capitalize()
        return { 'oid': oid,
                 'unit_of_measurement': unit_of_measurement,
                 'scale': scale,
                 'description': description,
               }
    def _get_volt_sensor_descriptions(self, row):
        row_oid = row.get(0, None)
        mib_object = self.nodes.get('ciscoEnvMonVoltageStatusValue', None)
        oid = str(mib_object.oid) + str(row_oid)
        unit_of_measurement = 'Volts'
        scale = self.mib.get('nodes').get(
                    'ciscoEnvMonVoltageStatusValue').get(
                    'units').strip().capitalize()
        scale = re.sub('volts$', '', scale)
        description = row.get('ciscoEnvMonVoltageStatusDescr', None)
        if description:
            description.strip().capitalize()
        return { 'oid': oid,
                 'unit_of_measurement': unit_of_measurement,
                 'scale': scale,
                 'description': description,
               }

    def get_sensor_descriptions(self, res):
        result = []
        for row_id, row in res.items():
            power_supply_source = row.get('ciscoEnvMonSupplySource', None)
            if power_supply_source:
                # power-supply sensor
                result.append(self._get_power_sensor_descriptions(row))
            fan_state = row.get('ciscoEnvMonFanState', None)
            if fan_state:
                result.append(self._get_fan_sensor_descriptions(row))
            temp_state = row.get('ciscoEnvMonTemperatureState', None)
            if temp_state:
                result.append(self._get_temp_sensor_descriptions(row))
            volt_state = row.get('ciscoEnvMonVoltageState', None)
            if volt_state:
                result.append(self._get_volt_sensor_descriptions(row))
        return result

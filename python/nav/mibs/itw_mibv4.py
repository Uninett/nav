# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Uninett AS
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
"""
A class that tries to retrieve all internal sensors from WeatherGoose II.

Uses the vendor-specifica IT-WATCHDOGS-V4-MIB to detect and collect
sensor-information.

Please note:
This is NOT a full implementaion of the IT-WATCHDOGS-V4-MIB. Only the internal
sensors of the box are implemented. The box can be extended with additional
external sensors, but these are not implemented because we did not have any
external sensors available at the time of this implementation.
"""
from django.utils.six import itervalues
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.smidumps import get_mib
from nav.mibs import mibretriever
from nav.models.manage import Sensor
from nav.oids import OID

TABLES = {
    'internalTable': [
        {
            'avail': 'internalAvail',
            'serial': 'internalSerial',
            'name': 'internalName',
            'sensors': {
                'internalTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'internalHumidity': dict(u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'internalDewPoint': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'internalIO1': dict(u_o_m=Sensor.UNIT_UNKNOWN),
                'internalIO2': dict(u_o_m=Sensor.UNIT_UNKNOWN),
                'internalIO3': dict(u_o_m=Sensor.UNIT_UNKNOWN),
                'internalIO4': dict(u_o_m=Sensor.UNIT_UNKNOWN),
            }
        }
    ],
    'tempSensorTable': [
        {
            'avail': 'tempSensorAvail',
            'serial': 'tempSensorSerial',
            'name': 'tempSensorName',
            'sensors': {
                'tempSensorTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'airFlowSensorTable': [
        {
            'avail': 'airFlowSensorAvail',
            'serial': 'airFlowSensorSerial',
            'name': 'airFlowSensorName',
            'sensors': {
                'airFlowSensorTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'airFlowSensorFlow': dict(u_o_m=Sensor.UNIT_UNKNOWN),
                'airFlowSensorHumidity': dict(u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'airFlowDewPoint': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'dewPointSensorTable': [
        {
            'avail': 'dewPointSensorAvail',
            'serial': 'dewPointSensorSerial',
            'name': 'dewPointSensorName',
            'sensors': {
                'dewPointSensorTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'dewPointSensorHumidity': dict(u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'dewPointDewPoint': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    't3hdSensorTable': [
        {
            'avail': 't3hdSensorAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorIntName',
            'sensors': {
                't3hdSensorIntSensorTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                't3hdSensorIntSensorHumidity': dict(u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                't3hdSensorIntDewPoint': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        },
        {
            'avail': 't3hdSensorExtAAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorExtAName',
            'sensors': {
                't3hdSensorExtATemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        },
        {
            'avail': 't3hdSensorExtBAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorExtBName',
            'sensors': {
                't3hdSensorExtBTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        },
        {
            'avail': 't3hdSensorExtCAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorExtCName',
            'sensors': {
                't3hdSensorExtCTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        },
    ],
    'thdSensorTable': [
        {
            'avail': 'thdSensorAvail',
            'serial': 'thdSensorSerial',
            'name': 'thdSensorName',
            'sensors': {
                'thdSensorTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'thdSensorHumidity': dict(u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'thdDewPoint': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'rpmSensorTable': [
        {
            'avail': 'rpmSensorAvail',
            'serial': 'rpmSensorSerial',
            'name': 'rpmSensorName',
            'sensors': {
                'rpmSensorEnergy': dict(u_o_m=Sensor.UNIT_WATTHOURS, scale=Sensor.SCALE_KILO),
                'rpmSensorVoltage': dict(u_o_m=Sensor.UNIT_VOLTS_DC),
                'rpmSensorCurrent': dict(precision=1, u_o_m=Sensor.UNIT_AMPERES),
                'rpmSensorRealPower': dict(u_o_m=Sensor.UNIT_WATTS),
                'rpmSensorApparentPower': dict(u_o_m=Sensor.UNIT_VOLTAMPERES),
                'rpmSensorPowerFactor': dict(u_o_m=Sensor.UNIT_PERCENT),
                'rpmSensorOutlet1': dict(u_o_m=Sensor.UNIT_TRUTHVALUE),
                'rpmSensorOutlet2': dict(u_o_m=Sensor.UNIT_TRUTHVALUE),
            }
        }
    ],
}


class ItWatchDogsMibV4(mibretriever.MibRetriever):
    """A class that tries to retrieve all sensors from Watchdog 100"""
    mib = get_mib('IT-WATCHDOGS-V4-MIB')

    def _get_oid_for_sensor(self, sensor_name):
        """Return the OID for the given sensor-name as a string; Return
        None if sensor-name is not found.
        """
        oid_str = None
        nodes = self.mib.get('nodes', None)
        if nodes:
            sensor_def = nodes.get(sensor_name, None)
            if sensor_def:
                oid_str = sensor_def.get('oid', None)
        return oid_str

    def _make_result_dict(self, sensor_oid, base_oid, serial, desc,
                          u_o_m=None, precision=0, scale=None, name=None):
        """ Make a simple dictionary to return to plugin"""
        if not sensor_oid or not base_oid or not serial or not desc:
            return {}
        oid = OID(base_oid) + OID(sensor_oid)
        internal_name = serial.decode('utf-8') + desc
        return {'oid': oid,
                'unit_of_measurement': u_o_m,
                'precision': precision,
                'scale': scale,
                'description': desc,
                'name': name,
                'internal_name': internal_name,
                'mib': self.get_module_name(),
                }

    def _handle_sensor_group(self, sensor_group, table_data):
        result = []
        avail_col = sensor_group['avail']
        name_col = sensor_group['name']
        serial_col = sensor_group['serial']
        sensor_conf = sensor_group['sensors']

        for row in itervalues(table_data):
            is_avail = row.get(avail_col)
            if is_avail:
                oid = row.get(0)
                serial = row.get(serial_col)
                name = row.get(name_col)
                for sensor, conf in sensor_conf.items():
                    result.append(self._make_result_dict(
                        oid,
                        self._get_oid_for_sensor(sensor),
                        serial, sensor, name=name, **conf))

        return result

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ Try to retrieve all internal available sensors in this WxGoose"""

        result = []
        for table, sensor_groups in TABLES.items():
            self._logger.debug('get_all_sensors: table = %s', table)
            sensors = yield self.retrieve_table(
                                        table).addCallback(reduce_index)
            self._logger.debug('get_all_sensors: %s = %s', table, sensors)
            for sensor_group in sensor_groups:
                result.extend(self._handle_sensor_group(sensor_group, sensors))

        defer.returnValue(result)

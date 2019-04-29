# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 Uninett AS
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
#
"""
A class that tries to retrieve all sensors from WeatherGoose I.

Uses the vendor-specifica IT-WATCHDOGS-MIB to detect and collect
sensor-information.
"""
from django.utils.six import itervalues
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.smidumps import get_mib
from nav.mibs import mibretriever
from nav.models.manage import Sensor
from nav.oids import OID


TABLES = {
    'climateTable': [
        {
            'avail': 'climateAvail',
            'serial': 'climateSerial',
            'name': 'climateName',
            'sensors': {
                'climateTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'climateHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'climateAirflow': {},
                'climateLight': {},
                'climateSound': {},
                'climateIO1': {},
                'climateIO2': {},
                'climateIO3': {},
            }
        }
    ],
    'tempSensorTable': [
        {
            'avail': 'tempSensorAvail',
            'serial': 'tempSensorSerial',
            'name': 'tempSensorName',
            'sensors': {
                'tempSensorTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'airFlowSensorTable': [
        {
            'avail': 'airFlowSensorAvail',
            'serial': 'airFlowSensorSerial',
            'name': 'airFlowSensorName',
            'sensors': {
                'airFlowSensorTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'airFlowSensorFlow': {},
                'airFlowSensorHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
            }
        }
    ],
    'doorSensorTable': [
        {
            'avail': 'doorSensorAvail',
            'serial': 'doorSensorSerial',
            'name': 'doorSensorName',
            'sensors': {
                'doorSensorStatus': {},
            }
        }
    ],
    'waterSensorTable': [
        {
            'avail': 'waterSensorAvail',
            'serial': 'waterSensorSerial',
            'name': 'waterSensorName',
            'sensors': {
                'waterSensorDampness': {},
            }
        }
    ],
    'currentMonitorTable': [
        {
            'avail': 'currentMonitorAvail',
            'serial': 'currentMonitorSerial',
            'name': 'currentMonitorName',
            'sensors': {
                'currentMonitorAmps': dict(
                    u_o_m=Sensor.UNIT_AMPERES, scale='milli'),
            }
        }
    ],
    'millivoltMonitorTable': [
        {
            'avail': 'millivoltMonitorAvail',
            'serial': 'millivoltMonitorSerial',
            'name': 'millivoltMonitorName',
            'sensors': {
                'millivoltMonitorMV': dict(
                    u_o_m=Sensor.UNIT_VOLTS_DC, scale='milli'),
            }
        }
    ],
    'dewPointSensorTable': [
        {
            'avail': 'dewPointSensorAvail',
            'serial': 'dewPointSensorSerial',
            'name': 'dewPointSensorName',
            'sensors': {
                'dewPointSensorDewPoint': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'dewPointSensorTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'dewPointSensorHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
            }
        }
    ],
    'digitalSensorTable': [
        {
            'avail': 'digitalSensorAvail',
            'serial': 'digitalSensorSerial',
            'name': 'digitalSensorName',
            'sensors': {
                'digitalSensorDigital': {},
            }
        }
    ],
    'cpmSensorTable': [
        {
            'avail': 'cpmSensorAvail',
            'serial': 'cpmSensorSerial',
            'name': 'cpmSensorName',
            'sensors': {
                'cpmSensorStatus': {},
            }
        }
    ],
    'smokeAlarmTable': [
        {
            'avail': 'smokeAlarmAvail',
            'serial': 'smokeAlarmSerial',
            'name': 'smokeAlarmName',
            'sensors': {
                'smokeAlarmStatus': {},
            }
        }
    ],
    'neg48VdcSensorTable': [
        {
            'avail': 'neg48VdcSensorAvail',
            'serial': 'neg48VdcSensorSerial',
            'name': 'neg48VdcSensorName',
            'sensors': {
                'neg48VdcSensorVoltage': dict(u_o_m=Sensor.UNIT_VOLTS_DC),
            }
        }
    ],
    'pos30VdcSensorTable': [
        {
            'avail': 'pos30VdcSensorAvail',
            'serial': 'pos30VdcSensorSerial',
            'name': 'pos30VdcSensorName',
            'sensors': {
                'pos30VdcSensorVoltage': dict(u_o_m=Sensor.UNIT_VOLTS_DC),
            }
        }
    ],
    'analogSensorTable': [
        {
            'avail': 'analogSensorAvail',
            'serial': 'analogSensorSerial',
            'name': 'analogSensorName',
            'sensors': {
                'analogSensorAnalog': {},
            }
        }
    ],
    'powerMonitorTable': [
        {
            'avail': 'powMonAvail',
            'serial': 'powMonSerial',
            'name': 'powMonName',
            'sensors': {
                'powMonKWattHrs': dict(u_o_m=Sensor.UNIT_WATTHOURS),
                'powMonVolts': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonVoltMax': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonVoltMin': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonVoltPk': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonAmpsX10': dict(u_o_m=Sensor.UNIT_AMPERES),
                'powMonRealPow': {},
                'powMonAppPow': {},
                'powMonPwrFact': {},
                'powMonOutlet1': {},
                'powMonOutlet2': {},
            }
        }
    ],
    'powerOnlyTable': [
        {
            'avail': 'powerAvail',
            'serial': 'powerSerial',
            'name': 'powerName',
            'sensors': {
                'powerVolts': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powerAmps': dict(u_o_m=Sensor.UNIT_AMPERES),
                'powerRealPow': {},
                'powerAppPow': {},
                'powerPwrFactor': {},
            }
        }
    ],
    'power3ChTable': [
        {
            'avail': 'pow3ChAvail',
            'serial': 'pow3ChSerial',
            'name': 'pow3ChName',
            'sensors': {
                'pow3ChKWattHrs' + ch: dict(u_o_m=Sensor.UNIT_WATTHOURS),
                'pow3ChVolts' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltMax' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltMin' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltMin' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltPk' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChAmpsX10' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'pow3ChRealPow' + ch: {},
                'pow3ChAppPow' + ch: {},
                'pow3ChPwrFact' + ch: {},
            }
        }
        for ch in ('A', 'B', 'C')
    ],
    'outletTable': [
        {
            'avail': 'outletAvail',
            'serial': 'outletSerial',
            'name': 'outletName',
            'sensors': {
                'outlet1Status': {},
                'outlet2Status': {},
            }
        }
    ],
    'vsfcTable': [
        {
            'avail': 'vsfcAvail',
            'serial': 'vsfcSerial',
            'name': 'vsfcName',
            'sensors': {
                'vsfcSetPointC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcFanSpeed': dict(u_o_m=Sensor.UNIT_RPM),
                'vsfcIntTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt1TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt2TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt3TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt4TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'ctrl3ChTable': [
        {
            'avail': 'ctrl3ChAvail',
            'serial': 'ctrl3ChSerial',
            'name': 'ctrl3ChName',
            'sensors': {
                'ctrl3ChVolts' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'ctrl3ChVoltPk' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'ctrl3ChAmps' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrl3ChAmpPk' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrl3ChRealPow' + ch: dict(u_o_m=Sensor.UNIT_WATTS),
                'ctrl3ChAppPow' + ch: dict(u_o_m=Sensor.UNIT_VOLTAMPERES),
                'ctrl3ChPwrFact' + ch: {},
            }
        }
        for ch in ('A', 'B', 'C')
    ],
    'ctrlGrpAmpsTable': [
        {
            'avail': 'ctrlGrpAmpsAvail',
            'serial': 'ctrlGrpAmpsSerial',
            'name': 'ctrlGrpAmpsName',
            'sensors': {
                'ctrlGrpAmps' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
            }
        }
        for ch in ('A', 'B', 'C', 'D', 'E', 'F')
    ],
    'ctrlOutletTable': [
        {
            'avail': 'ctrlOutletName',  # this table has no Avail column.
            'serial': 'ctrlOutletGroup',  # and serial
            'name': 'ctrlOutletName',
            'sensors': {
                'ctrlOutletStatus': {},
                'ctrlOutletFeedback': {},
                'ctrlOutletPending': {},
                'ctrlOutletAmps': dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrlOutletUpDelay': {},
                'ctrlOutletDwnDelay': {},
                'ctrlOutletRbtDelay': {},
            }
        }
    ],
    'dstsTable': [
        {
            'avail': 'dstsAvail',
            'serial': 'dstsSerial',
            'name': 'dstsName',
            'sensors': {
                'dstsVolts' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_DC),
                'dstsAmps' + ch: dict(
                        u_o_m=Sensor.UNIT_AMPERES),
                'dstsSource' + ch + 'Active': {},
                'dstsPowerStatus' + ch: {},
                'dstsSource' + ch + 'TempC': {},
            }
        }
        for ch in ('A', 'B')
    ],
}


class BaseITWatchDogsMib(mibretriever.MibRetriever):

    def _get_oid_for_sensor(self, sensor_name):
        """Return the OID for the given sensor-name as a string; Return
        None if sensor-name is not found.
        """
        oid_str = None
        nodes = self.mib.get('nodes')
        if nodes:
            sensor_def = nodes.get(sensor_name)
            if sensor_def:
                oid_str = sensor_def.get('oid')
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
        for table, sensor_groups in self.TABLES.items():
            self._logger.debug('get_all_sensors: table = %s', table)
            sensors = yield self.retrieve_table(
                                        table).addCallback(reduce_index)
            self._logger.debug('get_all_sensors: %s = %s', table, sensors)
            for sensor_group in sensor_groups:
                result.extend(self._handle_sensor_group(sensor_group, sensors))

        defer.returnValue(result)


class ItWatchDogsMib(BaseITWatchDogsMib):
    """A class that tries to retrieve all sensors from WeatherGoose I"""
    mib = get_mib('IT-WATCHDOGS-MIB')
    TABLES = TABLES

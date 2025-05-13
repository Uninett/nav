# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2019 Uninett AS
# Copyright (C) 2022 Sikt
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

from django.utils.encoding import smart_str
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
                'climateTempC',
                'climateHumidity',
                'climateAirflow',
                'climateLight',
                'climateSound',
                'climateIO1',
                'climateIO2',
                'climateIO3',
            },
        }
    ],
    'tempSensorTable': [
        {
            'avail': 'tempSensorAvail',
            'serial': 'tempSensorSerial',
            'name': 'tempSensorName',
            'sensors': {
                'tempSensorTempC',
            },
        }
    ],
    'airFlowSensorTable': [
        {
            'avail': 'airFlowSensorAvail',
            'serial': 'airFlowSensorSerial',
            'name': 'airFlowSensorName',
            'sensors': {
                'airFlowSensorTempC',
                'airFlowSensorFlow',
                'airFlowSensorHumidity',
            },
        }
    ],
    'doorSensorTable': [
        {
            'avail': 'doorSensorAvail',
            'serial': 'doorSensorSerial',
            'name': 'doorSensorName',
            'sensors': {
                'doorSensorStatus',
            },
        }
    ],
    'waterSensorTable': [
        {
            'avail': 'waterSensorAvail',
            'serial': 'waterSensorSerial',
            'name': 'waterSensorName',
            'sensors': {
                'waterSensorDampness',
            },
        }
    ],
    'currentMonitorTable': [
        {
            'avail': 'currentMonitorAvail',
            'serial': 'currentMonitorSerial',
            'name': 'currentMonitorName',
            'sensors': {
                'currentMonitorAmps',
            },
        }
    ],
    'millivoltMonitorTable': [
        {
            'avail': 'millivoltMonitorAvail',
            'serial': 'millivoltMonitorSerial',
            'name': 'millivoltMonitorName',
            'sensors': {
                'millivoltMonitorMV',
            },
        }
    ],
    'dewPointSensorTable': [
        {
            'avail': 'dewPointSensorAvail',
            'serial': 'dewPointSensorSerial',
            'name': 'dewPointSensorName',
            'sensors': {
                'dewPointSensorDewPoint',
                'dewPointSensorTempC',
                'dewPointSensorHumidity',
            },
        }
    ],
    'digitalSensorTable': [
        {
            'avail': 'digitalSensorAvail',
            'serial': 'digitalSensorSerial',
            'name': 'digitalSensorName',
            'sensors': {
                'digitalSensorDigital',
            },
        }
    ],
    'cpmSensorTable': [
        {
            'avail': 'cpmSensorAvail',
            'serial': 'cpmSensorSerial',
            'name': 'cpmSensorName',
            'sensors': {
                'cpmSensorStatus',
            },
        }
    ],
    'smokeAlarmTable': [
        {
            'avail': 'smokeAlarmAvail',
            'serial': 'smokeAlarmSerial',
            'name': 'smokeAlarmName',
            'sensors': {
                'smokeAlarmStatus',
            },
        }
    ],
    'neg48VdcSensorTable': [
        {
            'avail': 'neg48VdcSensorAvail',
            'serial': 'neg48VdcSensorSerial',
            'name': 'neg48VdcSensorName',
            'sensors': {
                'neg48VdcSensorVoltage',
            },
        }
    ],
    'pos30VdcSensorTable': [
        {
            'avail': 'pos30VdcSensorAvail',
            'serial': 'pos30VdcSensorSerial',
            'name': 'pos30VdcSensorName',
            'sensors': {
                'pos30VdcSensorVoltage',
            },
        }
    ],
    'analogSensorTable': [
        {
            'avail': 'analogSensorAvail',
            'serial': 'analogSensorSerial',
            'name': 'analogSensorName',
            'sensors': {
                'analogSensorAnalog',
            },
        }
    ],
    'powerMonitorTable': [
        {
            'avail': 'powMonAvail',
            'serial': 'powMonSerial',
            'name': 'powMonName',
            'sensors': {
                'powMonKWattHrs',
                'powMonVolts',
                'powMonVoltMax',
                'powMonVoltMin',
                'powMonVoltPk',
                'powMonAmpsX10',
                'powMonRealPow',
                'powMonAppPow',
                'powMonPwrFact',
                'powMonOutlet1',
                'powMonOutlet2',
            },
        }
    ],
    'powerOnlyTable': [
        {
            'avail': 'powerAvail',
            'serial': 'powerSerial',
            'name': 'powerName',
            'sensors': {
                'powerVolts',
                'powerAmps',
                'powerRealPow',
                'powerAppPow',
                'powerPwrFactor',
            },
        }
    ],
    'power3ChTable': [
        {
            'avail': 'pow3ChAvail',
            'serial': 'pow3ChSerial',
            'name': 'pow3ChName',
            'sensors': {
                'pow3ChKWattHrs' + ch,
                'pow3ChVolts' + ch,
                'pow3ChVoltMax' + ch,
                'pow3ChVoltMin' + ch,
                'pow3ChVoltMin' + ch,
                'pow3ChVoltPk' + ch,
                'pow3ChAmpsX10' + ch,
                'pow3ChRealPow' + ch,
                'pow3ChAppPow' + ch,
                'pow3ChPwrFact' + ch,
            },
        }
        for ch in ('A', 'B', 'C')
    ],
    'outletTable': [
        {
            'avail': 'outletAvail',
            'serial': 'outletSerial',
            'name': 'outletName',
            'sensors': {
                'outlet1Status',
                'outlet2Status',
            },
        }
    ],
    'vsfcTable': [
        {
            'avail': 'vsfcAvail',
            'serial': 'vsfcSerial',
            'name': 'vsfcName',
            'sensors': {
                'vsfcSetPointC',
                'vsfcFanSpeed',
                'vsfcIntTempC',
                'vsfcExt1TempC',
                'vsfcExt2TempC',
                'vsfcExt3TempC',
                'vsfcExt4TempC',
            },
        }
    ],
    'ctrl3ChTable': [
        {
            'avail': 'ctrl3ChAvail',
            'serial': 'ctrl3ChSerial',
            'name': 'ctrl3ChName',
            'sensors': {
                'ctrl3ChVolts' + ch,
                'ctrl3ChVoltPk' + ch,
                'ctrl3ChAmps' + ch,
                'ctrl3ChAmpPk' + ch,
                'ctrl3ChRealPow' + ch,
                'ctrl3ChAppPow' + ch,
                'ctrl3ChPwrFact' + ch,
            },
        }
        for ch in ('A', 'B', 'C')
    ],
    'ctrlGrpAmpsTable': [
        {
            'avail': 'ctrlGrpAmpsAvail',
            'serial': 'ctrlGrpAmpsSerial',
            'name': 'ctrlGrpAmpsName',
            'sensors': {
                'ctrlGrpAmps' + ch,
            },
        }
        for ch in ('A', 'B', 'C', 'D', 'E', 'F')
    ],
    'ctrlOutletTable': [
        {
            'serial': 'ctrlOutletGroup',  # and serial
            'name': 'ctrlOutletName',
            'sensors': {
                'ctrlOutletStatus',
                'ctrlOutletFeedback',
                'ctrlOutletPending',
                'ctrlOutletAmps',
                'ctrlOutletUpDelay',
                'ctrlOutletDwnDelay',
                'ctrlOutletRbtDelay',
            },
        }
    ],
    'dstsTable': [
        {
            'avail': 'dstsAvail',
            'serial': 'dstsSerial',
            'name': 'dstsName',
            'sensors': {
                'dstsVolts' + ch,
                'dstsAmps' + ch,
                'dstsSource' + ch + 'Active',
                'dstsPowerStatus' + ch,
                'dstsSource' + ch + 'TempC',
            },
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

    def _make_result_dict(
        self, sensor_oid, base_oid, serial, desc, u_o_m=None, **kwargs
    ):
        """Make a simple dictionary to return to plugin"""
        if not sensor_oid or not base_oid or not serial or not desc:
            return {}
        oid = OID(base_oid) + OID(sensor_oid)
        internal_name = smart_str(serial) + desc
        res = {
            'oid': oid,
            'unit_of_measurement': u_o_m,
            'description': desc,
            'internal_name': internal_name,
            'mib': self.get_module_name(),
        }
        res.update(kwargs)
        return res

    def _handle_sensor_group(self, sensor_group, table_data):
        result = []
        avail_col = sensor_group.get('avail')
        name_col = sensor_group['name']
        serial_col = sensor_group['serial']
        sensors = sensor_group['sensors']

        for row in table_data.values():
            if not avail_col or row.get(avail_col):
                oid = row.get(0)
                serial = row.get(serial_col)
                name = row.get(name_col)
                for sensor in sensors:
                    conf = convert_units(self.mib, sensor)
                    conf.update(get_range(self.mib, sensor))
                    result.append(
                        self._make_result_dict(
                            oid,
                            self._get_oid_for_sensor(sensor),
                            serial,
                            sensor,
                            name=name,
                            **conf,
                        )
                    )

        return result

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Try to retrieve all internal available sensors in this WxGoose"""

        result = []
        for table, sensor_groups in self.TABLES.items():
            self._logger.debug('get_all_sensors: table = %s', table)
            sensors = yield self.retrieve_table(table).addCallback(reduce_index)
            self._logger.debug('get_all_sensors: %s = %s', table, sensors)
            for sensor_group in sensor_groups:
                result.extend(self._handle_sensor_group(sensor_group, sensors))

        return result


UNITS = {
    '%': {'u_o_m': Sensor.UNIT_PERCENT},
    '0.1 Amps': {
        'u_o_m': Sensor.UNIT_AMPERES,
        'precision': 1,
    },
    '0.1 Amps (rms)': {
        'u_o_m': Sensor.UNIT_AMPERES,
        'precision': 1,
    },
    '0.1 Degrees': {
        'u_o_m': Sensor.UNIT_CELSIUS,
        'precision': 1,
    },
    'Degrees Celsius': {
        'u_o_m': Sensor.UNIT_CELSIUS,
    },
    'kWh': {
        'u_o_m': Sensor.UNIT_WATTHOURS,
        'scale': Sensor.SCALE_KILO,
    },
    'millivolts': {
        'u_o_m': Sensor.UNIT_VOLTS_DC,
        'scale': Sensor.SCALE_MILLI,
    },
    'Volt-Amps': {
        'u_o_m': Sensor.UNIT_VOLTAMPERES,
    },
    'Volts': {
        'u_o_m': Sensor.UNIT_VOLTS_DC,
    },
    'Volts (rms)': {
        'u_o_m': Sensor.UNIT_VOLTS_AC,
    },
    'Watts': {
        'u_o_m': Sensor.UNIT_WATTS,
    },
}


def get_range(mib, node):
    res = {}
    range_ = mib['nodes'][node].get('syntax', {}).get('type', {}).get('range')
    if not range_:
        return res
    if 'min' not in range_ or 'max' not in range_:
        return res
    res['minimum'] = range_['min']
    res['maximum'] = range_['max']
    return res


def convert_units(mib, node):
    unit = mib['nodes'][node].get("units")
    if unit:
        if unit in UNITS:
            res = UNITS[unit].copy()
            if res['u_o_m'] == Sensor.UNIT_PERCENT and "Humid" in node:
                res['u_o_m'] = Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY
            return res
    if 'syntax' not in mib['nodes'][node]:
        return {'u_o_m': Sensor.UNIT_TRUTHVALUE}
    return {'u_o_m': Sensor.UNIT_UNKNOWN}


class ItWatchDogsMib(BaseITWatchDogsMib):
    """A class that tries to retrieve all sensors from WeatherGoose I"""

    mib = get_mib('IT-WATCHDOGS-MIB')
    TABLES = TABLES

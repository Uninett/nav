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
"""

from nav.smidumps import get_mib
from nav.mibs.itw_mib import BaseITWatchDogsMib
from nav.models.manage import Sensor

TABLES = {
    'internalTable': [
        {
            'avail': 'internalAvail',
            'serial': 'internalSerial',
            'name': 'internalName',
            'sensors': {
                'internalTemp': dict(precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'internalHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'internalDewPoint': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
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
                'airFlowSensorTemp': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'airFlowSensorFlow': dict(u_o_m=Sensor.UNIT_UNKNOWN),
                'airFlowSensorHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'airFlowSensorDewPoint': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'dewPointSensorTable': [
        {
            'avail': 'dewPointSensorAvail',
            'serial': 'dewPointSensorSerial',
            'name': 'dewPointSensorName',
            'sensors': {
                'dewPointSensorTemp': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                'dewPointSensorHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'dewPointSensorDewPoint': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    't3hdSensorTable': [
        {
            'avail': 't3hdSensorAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorIntName',
            'sensors': {
                't3hdSensorIntTemp': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
                't3hdSensorIntHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                't3hdSensorIntDewPoint': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        },
        {
            'avail': 't3hdSensorExtAAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorExtAName',
            'sensors': {
                't3hdSensorExtATemp': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        },
        {
            'avail': 't3hdSensorExtBAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorExtBName',
            'sensors': {
                't3hdSensorExtBTemp': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
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
                'thdSensorHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'thdSensorDewPoint': dict(
                    precision=1, u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'rpmSensorTable': [
        {
            'avail': 'rpmSensorAvail',
            'serial': 'rpmSensorSerial',
            'name': 'rpmSensorName',
            'sensors': {
                'rpmSensorEnergy': dict(
                    u_o_m=Sensor.UNIT_WATTHOURS, scale=Sensor.SCALE_KILO),
                'rpmSensorVoltage': dict(u_o_m=Sensor.UNIT_VOLTS_DC),
                'rpmSensorCurrent': dict(
                    precision=1, u_o_m=Sensor.UNIT_AMPERES),
                'rpmSensorRealPower': dict(u_o_m=Sensor.UNIT_WATTS),
                'rpmSensorApparentPower': dict(u_o_m=Sensor.UNIT_VOLTAMPERES),
                'rpmSensorPowerFactor': dict(u_o_m=Sensor.UNIT_PERCENT),
                'rpmSensorOutlet1': dict(u_o_m=Sensor.UNIT_TRUTHVALUE),
                'rpmSensorOutlet2': dict(u_o_m=Sensor.UNIT_TRUTHVALUE),
            }
        }
    ],
}


class ItWatchDogsMibV4(BaseITWatchDogsMib):
    """A class that tries to retrieve all sensors from Watchdog 100"""
    mib = get_mib('IT-WATCHDOGS-V4-MIB')
    TABLES = TABLES

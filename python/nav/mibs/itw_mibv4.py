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

TABLES = {
    'internalTable': [
        {
            'avail': 'internalAvail',
            'serial': 'internalSerial',
            'name': 'internalName',
            'sensors': {
                'internalTemp',
                'internalHumidity',
                'internalDewPoint',
                'internalIO1',
                'internalIO2',
                'internalIO3',
                'internalIO4',
            }
        }
    ],
    'tempSensorTable': [
        {
            'avail': 'tempSensorAvail',
            'serial': 'tempSensorSerial',
            'name': 'tempSensorName',
            'sensors': {
                'tempSensorTemp',
            }
        }
    ],
    'airFlowSensorTable': [
        {
            'avail': 'airFlowSensorAvail',
            'serial': 'airFlowSensorSerial',
            'name': 'airFlowSensorName',
            'sensors': {
                'airFlowSensorTemp',
                'airFlowSensorFlow',
                'airFlowSensorHumidity',
                'airFlowSensorDewPoint',
            }
        }
    ],
    'dewPointSensorTable': [
        {
            'avail': 'dewPointSensorAvail',
            'serial': 'dewPointSensorSerial',
            'name': 'dewPointSensorName',
            'sensors': {
                'dewPointSensorTemp',
                'dewPointSensorHumidity',
                'dewPointSensorDewPoint',
            }
        }
    ],
    't3hdSensorTable': [
        {
            'avail': 't3hdSensorAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorIntName',
            'sensors': {
                't3hdSensorIntTemp',
                't3hdSensorIntHumidity',
                't3hdSensorIntDewPoint',
            }
        },
        {
            'avail': 't3hdSensorExtAAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorExtAName',
            'sensors': {
                't3hdSensorExtATemp',
            }
        },
        {
            'avail': 't3hdSensorExtBAvail',
            'serial': 't3hdSensorSerial',
            'name': 't3hdSensorExtBName',
            'sensors': {
                't3hdSensorExtBTemp',
            }
        },
    ],
    'thdSensorTable': [
        {
            'avail': 'thdSensorAvail',
            'serial': 'thdSensorSerial',
            'name': 'thdSensorName',
            'sensors': {
                'thdSensorTemp',
                'thdSensorHumidity',
                'thdSensorDewPoint',
            }
        }
    ],
    'rpmSensorTable': [
        {
            'avail': 'rpmSensorAvail',
            'serial': 'rpmSensorSerial',
            'name': 'rpmSensorName',
            'sensors': {
                'rpmSensorEnergy',
                'rpmSensorVoltage',
                'rpmSensorCurrent',
                'rpmSensorRealPower',
                'rpmSensorApparentPower',
                'rpmSensorPowerFactor',
                'rpmSensorOutlet1',
                'rpmSensorOutlet2',
            }
        }
    ],
}


class ItWatchDogsMibV4(BaseITWatchDogsMib):
    """A class that tries to retrieve all sensors from Watchdog 100"""
    mib = get_mib('IT-WATCHDOGS-V4-MIB')
    TABLES = TABLES

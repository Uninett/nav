#
# Copyright 2008 - 2011 (C) Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A class for extracting sensors from MGE UPSes."""

from nav.smidumps import get_mib
from nav.mibs.ups_mib import UpsMib
from nav.models.manage import Sensor


class MgSnmpUpsMib(UpsMib):
    """A custom class for retrieving sensors from MGE UPSes."""

    mib = get_mib('MG-SNMP-UPS-MIB')

    sensor_columns = {
        'mginputVoltage': {
            'u_o_m': Sensor.UNIT_VOLTS_AC,
            'precision': 1,
        },
        'mginputFrequency': {
            'u_o_m': Sensor.UNIT_HERTZ,
            'precision': 1,
        },
        'mgoutputLoadPerPhase': {
            'u_o_m': Sensor.UNIT_PERCENT,
        },
        'mgoutputCurrent': {
            'u_o_m': Sensor.UNIT_AMPERES,
        },
        'upsmgEnvironAmbientTemp': {
            'u_o_m': Sensor.UNIT_CELSIUS,
        },
        'upsmgBatteryLevel': {
            'u_o_m': Sensor.UNIT_PERCENT,
        },
        'upsmgBatteryRemainingTime': {
            'u_o_m': Sensor.UNIT_SECONDS,
        },
    }

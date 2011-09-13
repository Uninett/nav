#
# Copyright 2008 - 2011 (C) UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
""" A class for extracting sensors from APC UPSes.
"""
from nav.mibs.ups_mib import UpsMib

class PowerNetMib(UpsMib):
    """ Custom class for retrieveing sensors from APC UPSes."""
    from nav.smidumps.powernet_mib import MIB as mib

    sensor_columns = {
        'atsInputVoltage': {
            'u_o_m': 'Volts',
        },
        'upsAdvInputFrequency': {
            'u_o_m': 'Hz',
        },
        'upsAdvOutputCurrent': {
            'u_o_m': 'Amperes',
        },
        'mUpsEnvironAmbientTemperature': {
            'u_o_m': 'Celsius',
        },
        'upsAdvBatteryCapacity': {
            'u_o_m': 'Percent',
        },
        'upsBasicBatteryTimeOnBattery': {
            'u_o_m': 'Timeticks: second = timeticks/100',
        },
    }

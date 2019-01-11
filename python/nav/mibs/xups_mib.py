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
""" A class for extracting sensors from EATON UPSes.
"""
from nav.mibs.ups_mib import UpsMib


class XupsMib(UpsMib):
    """ A custom class for retrieving sensors from EATON UPSes."""
    from nav.smidumps.xups_mib import MIB as mib

    sensor_columns = {
        'xupsInputVoltage': {
            'u_o_m': 'Volts',
        },
        'xupsInputFrequency': {
            'u_o_m': 'Hz',
        },
        'xupsOutputCurrent': {
            'u_o_m': 'Amperes',
        },
        'xupsEnvAmbientTemp': {
            'u_o_m': 'Celsius',
        },
        'xupsBatCapacity': {
            'u_o_m': 'Percent',
        },
        'xupsBatTimeRemaining': {
            'u_o_m': 'Seconds',
        },
    }

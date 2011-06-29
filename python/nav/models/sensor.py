# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django ORM wrapper for the NAV manage database"""

from django.db import models

from nav.models.manage import Netbox
from nav.models.fields import VarcharField

class Sensor(models.Model):
    """
    This table contains meta-data about available sensors in
    network-equipment.

    Information in this table is used to make configurations for
    Cricket,- and Cricket maintain the resulting RRD-files for
    statistics.
    """

    UNIT_OTHER = 'other'        # Other than those listed
    UNIT_UNKNOWN = 'unknown'    # unknown measurement, or arbitrary,
                                # relative numbers
    UNIT_VOLTS_AC = 'voltsAC'   # electric potential
    UNIT_VOLTS_DC = 'voltsDC'    # electric potential
    UNIT_AMPERES = 'amperes'    # electric current
    UNIT_WATTS = 'watts'        # power
    UNIT_HERTZ = 'hertz'        # frequency
    UNIT_CELSIUS = 'celsius'    # temperature
    UNIT_PERCENT_RELATIVE_HUMIDITY = 'percentRH' # percent relative humidity
    UNIT_RPM = 'rpm'            # shaft revolutions per minute
    UNIT_CMM = 'cmm'            # cubic meters per minute (airflow)
    UNIT_TRUTHVALUE = 'boolean' # value takes { true(1), false(2) }
    
    UNIT_OF_MEASUREMENTS_CHOICES =(
        (UNIT_OTHER, 'Other'),
        (UNIT_UNKNOWN, 'Unknown'),
        (UNIT_VOLTS_AC, 'VoltsAC'),
        (UNIT_VOLTS_DC, 'VoltsDC'),
        (UNIT_AMPERES, 'Amperes'),
        (UNIT_WATTS, 'Watts'),
        (UNIT_HERTZ, 'Hertz'),
        (UNIT_CELSIUS, 'Celsius'),
        (UNIT_PERCENT_RELATIVE_HUMIDITY, 'Relative humidity'),
        (UNIT_RPM, 'Revolutions per minute'),
        (UNIT_CMM, 'Cubic meters per minute'),
        (UNIT_TRUTHVALUE, 'Boolean'),
    )

    SCALE_YOCTO = 'yocto' # 10^-24
    SCALE_ZEPTO = 'zepto' # 10^-21
    SCALE_ATTO = 'atto'   # 10^-18
    SCALE_FEMTO = 'femto' # 10^-15
    SCALE_PICO = 'pico'   # 10^-12
    SCALE_NANO = 'nano'   # 10^-9
    SCALE_MICRO = 'micro' # 10^-6
    SCALE_MILLI = 'milli' # 10^-3
    SCALE_UNITS = 'units' # 10^0
    SCALE_KILO = 'kilo'   # 10^3
    SCALE_MEGA = 'mega'   # 10^6
    SCALE_GIGA = 'giga'   # 10^9
    SCALE_TERA = 'tera'   # 10^12
    SCALE_EXA = 'exa'     # 10^15
    SCALE_PETA = 'peta'   # 10^18
    SCALE_ZETTA = 'zetta' # 10^21
    SCALE_YOTTA = 'yotta' # 10^24

    DATA_SCALE_CHOICES = (
        (SCALE_YOCTO, 'Yocto'),
        (SCALE_ZEPTO, 'Zepto'),
        (SCALE_ATTO, 'Atto'),
        (SCALE_FEMTO, 'Femto'),
        (SCALE_PICO, 'Pico'),
        (SCALE_NANO, 'Nano'),
        (SCALE_MICRO, 'Micro'),
        (SCALE_MILLI, 'Milli'),
        (SCALE_UNITS, 'No unit scaling'),
        (SCALE_KILO, 'Kilo'),
        (SCALE_MEGA, 'Mega'),
        (SCALE_GIGA, 'Giga'),
        (SCALE_TERA, 'Tera'),
        (SCALE_EXA, 'Exa'),
        (SCALE_PETA, 'Peta'),
        (SCALE_ZETTA, 'Zetta'),
        (SCALE_YOTTA, 'Yotta'),
    )

    id = models.AutoField(db_column='sensorid', primary_key=True)
    netbox = models.ForeignKey(Netbox, db_column='netboxid')
    oid = VarcharField(db_column="oid")
    unit_of_measurement = VarcharField(db_column="unit_of_measurement",
                                        choices=UNIT_OF_MEASUREMENTS_CHOICES)
    data_scale = VarcharField(db_column="data_scale",
                                choices=DATA_SCALE_CHOICES)
    human_readable = VarcharField(db_column="human_readable")
    name = VarcharField(db_column="name")
    internal_name = VarcharField(db_column="internal_name")
    mib = VarcharField(db_column="mib")

    class Meta:
        db_table = 'sensor'

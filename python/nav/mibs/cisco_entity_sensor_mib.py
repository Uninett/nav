#
# Copyright (C) 2009-2012 Uninett AS
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
from nav.smidumps import get_mib
from nav.mibs.entity_sensor_mib import EntitySensorMib


class CiscoEntitySensorMib(EntitySensorMib):
    """This MIB should collect all present sensors from Cisco NEXUS boxes."""
    mib = get_mib('CISCO-ENTITY-SENSOR-MIB')
    TYPE_COLUMN = 'entSensorType'
    SCALE_COLUMN = 'entSensorScale'
    PRECISION_COLUMN = 'entSensorPrecision'
    VALUE_COLUMN = 'entSensorValue'
    STATUS_COLUMN = 'entSensorStatus'

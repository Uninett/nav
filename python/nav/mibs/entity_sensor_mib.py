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

from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs.entity_mib import EntityMib
from nav.smidumps import get_mib
from nav.mibs import mibretriever
from nav.models.manage import Sensor

UNITS_OF_MEASUREMENTS = {
    1: Sensor.UNIT_OTHER,
    2: Sensor.UNIT_UNKNOWN,
    3: Sensor.UNIT_VOLTS_AC,
    4: Sensor.UNIT_VOLTS_DC,
    5: Sensor.UNIT_AMPERES,
    6: Sensor.UNIT_WATTS,
    7: Sensor.UNIT_HERTZ,
    8: Sensor.UNIT_CELSIUS,
    9: Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY,
    10: Sensor.UNIT_RPM,
    11: Sensor.UNIT_CMM,
    12: Sensor.UNIT_TRUTHVALUE,
    13: 'specialEnum',  # cisco extension
    14: Sensor.UNIT_DBM,  # cisco extension
}

DATA_SCALE = {
    1: 'yocto',
    2: 'zepto',
    3: 'atto',
    4: 'femto',
    5: 'pico',
    6: 'nano',
    7: 'micro',
    8: 'milli',
    9: None,
    10: 'kilo',
    11: 'mega',
    12: 'giga',
    13: 'tera',
    14: 'exa',
    15: 'peta',
    16: 'zetta',
    17: 'yotta',
}


class EntitySensorMib(mibretriever.MibRetriever):
    mib = get_mib('ENTITY-SENSOR-MIB')
    TYPE_COLUMN = 'entPhySensorType'
    SCALE_COLUMN = 'entPhySensorScale'
    PRECISION_COLUMN = 'entPhySensorPrecision'
    VALUE_COLUMN = 'entPhySensorValue'
    STATUS_COLUMN = 'entPhySensorOperStatus'

    def __init__(self, agent_proxy):
        """Good old constructor..."""
        super(EntitySensorMib, self).__init__(agent_proxy)
        self.entity_mib = EntityMib(self.agent_proxy)

    def _get_sensors(self):
        """Collect all sensors from the box."""
        df = self.retrieve_columns(
            [
                self.TYPE_COLUMN,
                self.SCALE_COLUMN,
                self.PRECISION_COLUMN,
                self.VALUE_COLUMN,
                self.STATUS_COLUMN,
            ]
        )
        df.addCallback(reduce_index)
        return df

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Collect all sensors and names on a netbox, and match
        sensors with names.

        Return a list with dictionaries, each dictionary
        represent a sensor."""
        sensors = yield self._get_sensors()
        entities = yield self.entity_mib.get_entity_physical_table()
        aliases = yield self.entity_mib.get_alias_mapping()
        for idx, row in entities.items():
            if idx in sensors:
                sensors[idx]['entPhysicalDescr'] = row.get('entPhysicalDescr')
                sensors[idx]['entPhysicalName'] = row.get('entPhysicalName')
                port = entities.get_nearest_port_parent(row)
                if port and port.index[-1] in aliases:
                    ifindices = aliases[port.index[-1]]
                    if len(ifindices) == 1:
                        sensors[idx]['ifindex'] = ifindices[0]
        result = []
        for row_id, row in sensors.items():
            row_oid = row.get(0)
            mibobject = self.nodes.get(self.VALUE_COLUMN)
            oid = str(mibobject.oid) + str(row_oid)
            unit_of_measurement = row.get(self.TYPE_COLUMN, 2)
            precision = row.get(self.PRECISION_COLUMN, 0)
            scale = row.get(self.SCALE_COLUMN)
            op_status = row.get(self.STATUS_COLUMN)
            description = row.get('entPhysicalDescr')
            name = row.get('entPhysicalName') or description
            ifindex = row.get('ifindex')
            internal_name = name
            if op_status == 1:
                result.append(
                    {
                        'oid': oid,
                        'unit_of_measurement': UNITS_OF_MEASUREMENTS.get(
                            unit_of_measurement
                        ),
                        'precision': precision,
                        'scale': DATA_SCALE.get(scale),
                        'description': description,
                        'name': name,
                        'internal_name': internal_name,
                        'mib': self.get_module_name(),
                        'ifindex': ifindex,
                    }
                )
        self._logger.debug('get_all_sensors: result=%s', result)
        return result

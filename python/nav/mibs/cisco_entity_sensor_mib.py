#
# Copyright (C) 2009-2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Implements a MibRetriever for the ENTITY-MIB, as well as helper classes."""

from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs.entity_mib import EntityMib
from nav.mibs import mibretriever

UNITS_OF_MEASUREMENTS = {
    1: 'other',
    2: 'unknown',
    3: 'voltsAC',
    4: 'voltsDC',
    5: 'amperes',
    6: 'watts',
    7: 'hertz',
    8: 'celsius',
    9: 'percentRH',
    10: 'rpm',
    11: 'cmm',
    12: 'boolean',
    13: 'specialEnum',
    14: 'dBm',
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

class CiscoEntitySensorMib(mibretriever.MibRetriever):
    """This MIB should collect all present sensors from Cisco NEXUS boxes."""
    from nav.smidumps.cisco_entity_sensor_mib import MIB as mib

    def __init__(self, agent_proxy):
        """Good old constructor..."""
        super(CiscoEntitySensorMib, self).__init__(agent_proxy)
        self.entity_mib = EntityMib(self.agent_proxy)

    def get_module_name(self):
        """Get the name of this MIB"""
        return self.mib.get('moduleName', None)

    def _get_sensors(self):
        """ Collect all sensors from the box."""
        df = self.retrieve_columns([
                'entSensorType',
                'entSensorScale',
                'entSensorPrecision',
                'entSensorValue',
                'entSensorStatus',
                'entSensorValueTimeStamp',
                'entSensorValueUpdateRate',
                'entSensorMeasuredEntity',
                ])
        df.addCallback(reduce_index)
        return df

    def _collect_entity_names(self):
        """ Collect all entity-names in netbox."""
        df = self.entity_mib.retrieve_columns([
                'entPhysicalDescr',
                'entPhysicalName',
                ])
        df.addCallback(reduce_index)
        return df

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ Collect all sensors and names on a netbox, and match
            sensors with names.

            Return a list with dictionaries, each dictionary
            represent a sensor."""
        self._logger.debug('get_all_sensors: Called....')
        sensors = yield self._get_sensors()
        entity_names = yield self._collect_entity_names()
        for idx, row in entity_names.items():
            if idx in sensors:
                sensors[idx]['entPhysicalDescr'] = row.get(
                    'entPhysicalDescr',None)
                sensors[idx]['entPhysicalName'] = row.get(
                    'entPhysicalName', None)
        result = []
        for row_id, row in sensors.items():
            row_oid = row.get(0, None)
            mibobject = self.nodes.get('entSensorValue', None)
            oid = str(mibobject.oid) + str(row_oid)
            unit_of_measurement = row.get('entSensorType', 2)
            precision = row.get('entSensorPrecision', 0)
            scale = row.get('entSensorScale', None)
            op_status = row.get('entSensorStatus', None)
            description = row.get('entPhysicalDescr', None)
            name = row.get('entPhysicalName', None)
            internal_name = name
            if op_status == 1:
                result.append({
                    'oid': oid,
                    'unit_of_measurement': UNITS_OF_MEASUREMENTS.get(
                        unit_of_measurement, None),
                    'precision': precision,
                    'scale': DATA_SCALE.get(scale, None),
                    'description': description,
                    'name': name,
                    'internal_name': internal_name,
                    'mib': self.get_module_name(),
                    })
        self._logger.debug('get_all_sensors: result=%s' % str(result))
        defer.returnValue(result)

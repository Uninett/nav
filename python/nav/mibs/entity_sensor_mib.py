# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 UNINETT AS
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

from twisted.internet import defer
from twisted.internet import threads

from nav.mibs import reduce_index
from nav.mibs.entity_mib import EntityMib

import mibretriever

DATA_SCALE = {
    1: 'Yocto',
    2: 'Zepto',
    3: 'Atto',
    4: 'Femto',
    5: 'Pico',
    6: 'Nano',
    7: 'Micro',
    8: 'Milli',
    9: None,
   10: 'Kilo',
   11: 'Mega',
   12: 'Giga',
   13: 'Tera',
   14: 'Exa',
   15: 'Peta',
   16: 'Zetta',
   17: 'Yotta',
  }

class EntitySensorMib(mibretriever.MibRetriever):
    from nav.smidumps.entity_sensor_mib import MIB as mib

    def get_module_name(self):
        return self.mib.get('moduleName', None)

    def _get_sensors(self):
        """ Collect all sensors."""
        df = self.retrieve_columns([
                'entPhySensorType',
                'entPhySensorScale',
                'entPhySensorPrecision',
                'entPhySensorValue',
                'entPhySensorOperStatus',
                'entPhySensorUnitsDisplay',
                ])
        df.addCallback(reduce_index)
        return df
            
    def _collect_entity_names(self):
        """ Collect all entity-names on netbox."""
        entity_mib = EntityMib(self.agent_proxy)
        df = entity_mib.retrieve_columns([
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
            mibobject = self.nodes.get('entPhySensorValue', None)
            oid = str(mibobject.oid) + str(row_oid)
            unit_of_measurement = row.get('entPhySensorUnitsDisplay', None)
            scale = row.get('entPhySensorScale', None)
            op_status = row.get('entPhySensorOperStatus', None)
            sensor_type = row.get('entPhySensorType', None)
            description = row.get('entPhysicalDescr')
            name = row.get('entPhysicalName', None)
            internal_name = name
            if op_status == 1:
                result.append({
                            'oid': oid,
                            'unit_of_measurement': unit_of_measurement,
                            'scale': DATA_SCALE.get(scale, None),
                            'description': description,
                            'name': name,
                            'internal_name': internal_name,
                            'mib': self.get_module_name(),
                            })
        self.logger.error('get_all_sensors: result=%s' % result)
        defer.returnValue(result)

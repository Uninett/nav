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
import mibretriever

SENSOR_TYPE ={
    1: 'Other',
    2: 'Unknown',
    3: 'VoltsAC',
    4: 'VoltsDC',
    5: 'Amperes',
    6: 'Watts',
    7: 'Hertz',
    8: 'Celsius',
    9: 'Relative humidity',
   10: 'RPM',
   11: 'Airflow',
   12: 'Boolean',
  }

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
    
    def retrieve_std_columns(self):
        """ A convenient function for getting the most interesting
        columns for environment mibs. """
        return self.retrieve_columns([
                'entPhySensorType',
                'entPhySensorScale',
                'entPhySensorPrecision',
                'entPhySensorValue',
                'entPhySensorOperStatus',
                'entPhySensorUnitsDisplay',
                ])

    def get_module_name(self):
        return self.mib.get('moduleName', None)
    
    def get_sensor_descriptions(self, res):
        result = []
        for row_id, row in res.items():
            row_oid = row.get(0, None)
            mibobject = self.nodes.get('entPhySensorValue', None)
            oid = str(mibobject.oid) + str(row_oid)
            unit_of_measurement = row.get('entPhySensorUnitsDisplay', None)
            scale = row.get('entPhySensorScale', None)
            op_status = row.get('entPhySensorOperStatus', None)
            sensor_type = row.get('entPhySensorType', None)
            if op_status == 1:
                result.append({
                            'oid': oid,
                            'unit_of_measurement': unit_of_measurement,
                            'scale': DATA_SCALE.get(scale, None),
                            'description': SENSOR_TYPE.get(sensor_type,None),
                            })
        return result

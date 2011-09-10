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
""" A class for extracting sensors from EATON UPSes.
"""
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever

class XupsMib(mibretriever.MibRetriever):
    from nav.smidumps.xups_mib import MIB as mib

    def get_module_name(self):
        """Return the MIB-name."""
        return self.mib.get('moduleName', None)

    def _get_input_voltage_sensors(self):
        """ volts """
        df = self.retrieve_columns(['xupsInputVoltage'])
        df.addCallback(reduce_index)
        return df

    def _get_input_frequency_sensors(self):
        """ Hz """
        df = self.retrieve_columns(['xupsInputFrequency'])
        df.addCallback(reduce_index)
        return df

    def _get_output_current_sensors(self):
        """ amperes """
        df = self.retrieve_columns(['xupsOutputCurrent'])
        df.addCallback(reduce_index)
        return df

    def _get_temp_sensors(self):
        """ celsius """
        df = self.retrieve_columns(['xupsEnvAmbientTemp'])
        df.addCallback(reduce_index)
        return df

    def _get_battery_level_sensors(self):
        """ percent """
        df = self.retrieve_columns(['xupsBatCapacity'])
        df.addCallback(reduce_index)
        return df

    def _get_battery_time_sensors(self):
        """ seconds """
        df = self.retrieve_columns(['xupsBatTimeRemaining'])
        df.addCallback(reduce_index)
        return df

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ .... """
        temp_sensors = yield self._get_temp_sensors()
        result = []
        for row_id, row in temp_sensor.items():
            row_oid = row.get(0, None)
            mibobject = self.nodes.get('xupsEnvAmbientTemp', None)
            oid = str(mibobject.oid) + str(row_oid)
            unit_of_measurement = 'celsius'
            precision = None
            scale = None
            description = 'ambient temperature'
            name = 'xupsEnvAmbientTemp'
            internal_name = name
            result.append( {
                    'oid': oid,
                    'unit_of_measurement': unit_of_measurement,
                    'precision': precision,
                    'scale': scale,
                    'description': description,
                    'name': name,
                    'internal_name': internal_name,
                    'mib': self.get_module_name(),
                    })
        return result

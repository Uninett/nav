#
# Copyright 2008 - 2011, 2014 (C) Uninett AS
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
"""A class for extracting sensors from RFC1628 compatible UPSes"""
from django.utils.six import itervalues
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever


class UpsMib(mibretriever.MibRetriever):
    """ A class for retrieveing sensors from RFC1628-compatible UPSes."""
    from nav.smidumps.ups_mib import MIB as mib

    sensor_columns = {
        # battery group
        'upsBatteryTemperature': {
            'u_o_m': 'Celsius',
        },
        'upsEstimatedChargeRemaining': {
            'u_o_m': 'Percent',
        },
        'upsEstimatedMinutesRemaining': {
            'u_o_m': 'Minutes',
        },

        # input group
        'upsInputNumLines': {},

        'upsInputFrequency': {
            'is_column': True,
            'u_o_m': 'Hz',
            'precision': 1,
        },
        'upsInputVoltage': {
            'is_column': True,
            'u_o_m': 'Volts',
        },
        'upsInputCurrent': {
            'is_column': True,
            'u_o_m': 'Amperes',
            'precision': 1,
        },
        'upsInputTruePower': {
            'is_column': True,
            'u_o_m': 'Watts',
        },

        # output group
        'upsOutputFrequency': {
            'u_o_m': 'Hz',
            'precision': 1,
        },
        'upsOutputNumLines': {},

        'upsOutputVoltage': {
            'is_column': True,
            'u_o_m': 'Volts',
        },
        'upsOutputCurrent': {
            'is_column': True,
            'u_o_m': 'Amperes',
            'precision': 1,
        },
        'upsOutputPower': {
            'is_column': True,
            'u_o_m': 'Watts',
        },
        'upsOutputPercentLoad': {
            'is_column': True,
            'u_o_m': 'Percent',
        },

        # bypass group
        'upsBypassFrequency': {
            'u_o_m': 'Hz',
            'precision': 1
        },
        'upsBypassNumLines': {},

        'upsBypassVoltage': {
            'is_column': True,
            'u_o_m': 'Volts',
        },
        'upsBypassCurrent': {
            'is_column': True,
            'u_o_m': 'Amperes',
            'precision': 1,
        },
        'upsBypassPower': {
            'is_column': True,
            'u_o_m': 'Watts',
        },
    }

    def _get_named_column(self, column):
        """Retrieves the contents of the named column from this MIB"""
        df = self.retrieve_columns([column])
        df.addCallback(reduce_index)
        return df

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Returns a list of all the interesting sensors on this UPS."""
        result = []

        for sensor in self.sensor_columns.keys():
            sensor_params = yield self._get_named_column(sensor)
            result.extend(self._get_sensors(sensor, sensor_params))

        defer.returnValue(result)

    def _get_sensors(self, object_name, sensor_params):
        result = []
        meta = self.sensor_columns[object_name]
        self._logger.debug('_get_sensors: %s; %s = %s',
                           self.agent_proxy.ip, object_name, sensor_params)

        for row in itervalues(sensor_params):
            row_oid = row.get(0, None)
            mibobject = self.nodes.get(object_name, None)
            oid = str(mibobject.oid) + str(row_oid)
            unit_of_measurement = meta.get('u_o_m', None)
            precision = meta.get('precision', None)
            scale = meta.get('scale', None)
            description = self.mib.get('nodes').get(object_name).get(
                'description', None)
            if meta.get('is_column', False):
                name = object_name + str(row_oid)
            else:
                name = object_name
            internal_name = name

            result.append({
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

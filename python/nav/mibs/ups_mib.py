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
""" A class for extracting sensors from RFC1628-compatible UPSes.
"""
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever


class UpsMib(mibretriever.MibRetriever):
    """ A class for retrieveing sensors from RFC1628-compatible UPSes."""
    from nav.smidumps.ups_mib import MIB as mib

    sensor_columns = {
        'upsInputVoltage': {
            'u_o_m': 'Volts',
            },
        'upsInputFrequency': {
            'u_o_m': 'Hz',
            },
        'upsOutputCurrent': {
            'u_o_m': 'Amperes',
            },
        'upsBatteryTemperature': {
            'u_o_m': 'Celsius',
            },
        'upsEstimatedChargeRemaining': {
            'u_o_m': 'Percent',
            },
        'upsEstimatedMinutesRemaining': {
            'u_o_m': 'Minutes',
            },
        }

    def get_module_name(self):
        """return the MIB-name."""
        return self.mib.get('moduleName', None)

    def _get_named_column(self, column):
        """ Return the named column in this mib"""
        df = self.retrieve_columns([column])
        df.addCallback(reduce_index)
        return df

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ Get all the interesting sensors for this UPS."""
        result = []
        for sensor_name in self.sensor_columns.keys():
            sensor_params = yield self._get_named_column(sensor_name)
            self.logger.debug('UpsMib:: get_all_sensors: ip = %s' %
                    self.agent_proxy.ip)
            self.logger.debug('UpsMib:: get_all_sensors: %s = %s' %
                (sensor_name, sensor_params))
            for row_id, row in sensor_params.items():
                row_oid = row.get(0, None)
                mibobject = self.nodes.get(sensor_name, None)
                oid = str(mibobject.oid) + str(row_oid)
                unit_of_measurement = self.sensor_columns[sensor_name].get(
                                                                'u_o_m', None)
                precision = self.sensor_columns[sensor_name].get(
                                                            'precision', None)
                scale = self.sensor_columns[sensor_name].get('scale', None)
                description = self.mib.get('nodes').get(sensor_name).get(
                                                           'description', None)
                name = sensor_name
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
        defer.returnValue(result)

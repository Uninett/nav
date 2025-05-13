#
# Copyright (C) 2014 Uninett AS
# Copyright (C) 2022 Sikt
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
"""
AKCP SPAGENT-MIB MibRetriever.

Not all sensor types of the sensorProbe product range are supported by this
implementation. sensorProbes support a multitude of switch sensors and virtual
sensors, whose readouts aren't suitable for graphing over time.

This implementation sticks with the easily graphable sensors,
like temperature, humidity, voltages and currents.

"""

from twisted.internet import defer
from nav.mibs import reduce_index
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

PRODUCT_TYPE = "sensorProbeProductType"

AKCP_SENSOR_PROBE_8_TABLES = {
    'sensorProbeTempTable': {
        'descr': 'sensorProbeTempDescription',
        'online': 'sensorProbeTempOnline',
        'unit': 'sensorProbeTempDegreeType',
        'readout': 'sensorProbeTempDegreeRaw',
        'precision': 1,
        'internal_prefix': 'temperature',
    },
    'sensorProbeHumidityTable': {
        'descr': 'sensorProbeHumidityDescription',
        'online': 'sensorProbeHumidityOnline',
        '_unit': Sensor.UNIT_PERCENT,
        'readout': 'sensorProbeHumidityPercent',
        'precision': 0,
        'internal_prefix': 'humidity',
    },
    # 'sensorProbeSwitchTable': {},  # wouldn't know how to graph this
    'sensorProbeIRMSSensorTable': {
        'descr': 'sensorProbeIRMSDescription',
        'online': 'sensorProbeIRMSOnline',
        '_unit': Sensor.UNIT_PERCENT,
        'readout': 'sensorProbeIRMSPercent',
        'precision': 0,
        'internal_prefix': 'IRMSsensor',
    },
    'sensorProbeVRMSSensorTable': {
        'descr': 'sensorProbeVRMSDescription',
        'online': 'sensorProbeVRMSOnline',
        '_unit': Sensor.UNIT_PERCENT,
        'readout': 'sensorProbeVRMSPercent',
        'precision': 0,
        'internal_prefix': 'VRMSsensor',
    },
    'sensorProbeEnergySensorTable': {
        'descr': 'sensorProbeEnergyDescription',
        'online': 'sensorProbeEnergyOnline',
        '_unit': Sensor.UNIT_PERCENT,
        'readout': 'sensorProbeEnergyPercent',
        'precision': 0,
        'internal_prefix': 'energysensor',
    },
}

AKCP_SENSOR_PROBE_PLUS_TABLES = {
    'commonTable': {
        'descr': 'commonDescription',
        'readout': 'commonValue',
        'unit': 'commonUnit',
        'precision': 0,
        'internal_prefix': 'common',
    }
}


# maps PRODUCT_TYPE to relevant tables
TABLES = {
    2: AKCP_SENSOR_PROBE_8_TABLES,
    16: AKCP_SENSOR_PROBE_PLUS_TABLES,
}


class SPAgentMib(MibRetriever):
    """SPAGENT-MIB MibRetriever"""

    mib = get_mib('SPAGENT-MIB')

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Returns a Deferred whose result is a list of sensor dictionaries"""
        result = []
        model_id = yield self.get_next(PRODUCT_TYPE)
        if model_id not in TABLES.keys():
            # default to the older version
            model_id = 2
        for table, config in TABLES[model_id].items():
            sensors = yield self._get_sensors(config)
            result.extend(sensors)
        return result

    @defer.inlineCallbacks
    def _get_sensors(self, config):
        """
        Collects sensor columns according to the config dict, and translates
        the results into sensor dicts.

        """
        columns = [config['descr']]
        for field in ['unit', 'online']:
            if field in config:
                columns.append(config[field])

        result = (
            yield self.retrieve_columns(columns)
            .addCallback(self.translate_result)
            .addCallback(reduce_index)
        )

        sensors = (
            self._row_to_sensor(config, index, row) for index, row in result.items()
        )

        return [s for s in sensors if s]

    def _row_to_sensor(self, config, index, row):
        """
        Converts a collect SNMP table row into a sensor dict, using the
        options defined in the config dict.

        """
        if 'online' in config:
            online = row.get(config['online'], 'offline')
            if online == 'offline':
                return

        internal_name = config['internal_prefix'] + str(index)
        descr = row.get(config['descr'], internal_name)

        mibobject = self.nodes.get(config['readout'])
        readout_oid = str(mibobject.oid + str(index))

        if 'unit' in config:
            unit = row.get(config['unit'], None)
            if unit == 'fahr':
                unit = Sensor.UNIT_FAHRENHEIT
            if unit == 'C':
                unit = Sensor.UNIT_CELSIUS
        else:
            unit = config['_unit']

        return {
            'oid': readout_oid,
            'unit_of_measurement': unit,
            'precision': config['precision'],
            'scale': None,
            'description': descr,
            'name': descr,
            'internal_name': internal_name,
            'mib': 'SPAGENT-MIB',
        }

#
# Copyright (C) 2019 Uninett AS
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
"""A class for extracting information from HPE power devices devices"""

from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs import reduce_index
from nav.models.manage import Sensor
from . import mibretriever

SENSORS = [
    {
        'extra_columns': [
            'pdu3GroupName',
            'pdu3GroupVoltageMeasType',
            'pdu3groupCurrentRating',
        ],
        'filter': lambda x: x.get('pdu3GroupName') is not None
        and x.get('pdu3GroupVoltageMeasType'),
        'sensors': {
            'pdu3GroupVoltage': {
                'description': '{pdu3GroupName} Voltage ({pdu3GroupVoltageMeasType})',
                'unit_of_measurement': Sensor.UNIT_VOLTS_AC,
                'precision': 1,
                'name': 'Group {pdu3GroupName} Voltage',
            },
            'pdu3GroupCurrent': {
                'unit_of_measurement': Sensor.UNIT_AMPERES,
                'precision': 2,
                'name': 'Group {pdu3GroupName} Current',
                'minimum': 0,
                'maximum': lambda x: (
                    x.get('pdu3groupCurrentRating') / 100
                    if x.get('pdu3groupCurrentRating') > 0
                    else None
                ),
            },
            'pdu3GroupPowerVA': {
                'unit_of_measurement': Sensor.UNIT_VOLTAMPERES,
                'name': 'Group {pdu3GroupName} Apperant Power',
            },
            'pdu3GroupPowerWatts': {
                'unit_of_measurement': Sensor.UNIT_WATTS,
                'name': 'Group {pdu3GroupName} Real Power',
            },
            "pdu3GroupPowerWattHour": {
                'unit_of_measurement': Sensor.UNIT_WATTHOURS,
                'name': 'Group {pdu3GroupName} Energy usage',
                'scale': Sensor.SCALE_KILO,
            },
            "pdu3GroupPowerFactor": {
                'unit_of_measurement': Sensor.UNIT_PERCENT,
                'name': 'Group {pdu3GroupName} Power Factor',
            },
            "pdu3GroupPowerVAR": {
                'unit_of_measurement': Sensor.UNIT_VAR,
                'name': 'Group {pdu3GroupName} Reactive Power',
            },
        },
    },
    {
        'extra_columns': [
            'pdu3InputPhaseVoltageMeasType',
            'pdu3InputPhaseCurrentRating',
            'pdu3InputPhaseCurrentMeasType',
            'pdu3InputPhasePowerMeasType',
        ],
        'sensors': {
            'pdu3InputPhaseVoltage': {
                'name': 'Input {pdu3InputPhaseVoltageMeasType} Voltage',
                'unit_of_measurement': Sensor.UNIT_VOLTS_AC,
                'precision': 1,
            },
            'pdu3InputPhaseCurrent': {
                'unit_of_measurement': Sensor.UNIT_AMPERES,
                'precision': 2,
                'name': 'Input {pdu3InputPhaseCurrentMeasType} Current',
                'minimum': 0,
                'maximum': lambda x: (
                    x.get('pdu3InputPhaseCurrentRating') / 100
                    if x.get('pdu3InputPhaseCurrentRating') > 0
                    else None
                ),
            },
            'pdu3InputPhasePowerVA': {
                'unit_of_measurement': Sensor.UNIT_VOLTAMPERES,
                'name': 'Input {pdu3InputPhasePowerMeasType} Apperant Power',
            },
            'pdu3InputPhasePowerWatts': {
                'unit_of_measurement': Sensor.UNIT_WATTS,
                'name': 'Input {pdu3InputPhasePowerMeasType} Real Power',
            },
            "pdu3InputPhasePowerWattHour": {
                'unit_of_measurement': Sensor.UNIT_WATTHOURS,
                'name': 'Input {pdu3InputPhasePowerMeasType} Energy usage',
                'scale': Sensor.SCALE_KILO,
            },
            "pdu3InputPhasePowerFactor": {
                'unit_of_measurement': Sensor.UNIT_PERCENT,
                'name': 'Input {pdu3InputPhasePowerMeasType} Power Factor',
            },
            "pdu3InputPhasePowerVAR": {
                'unit_of_measurement': Sensor.UNIT_VAR,
                'name': 'Input {pdu3InputPhasePowerMeasType} Reactive Power',
            },
        },
    },
    {
        'sensors': {
            'pdu3InputPowerVA': {
                'unit_of_measurement': Sensor.UNIT_VOLTAMPERES,
                'name': 'Total Input Apperant Power',
            },
            'pdu3InputPowerWatts': {
                'unit_of_measurement': Sensor.UNIT_WATTS,
                'name': 'Total Input Real Power',
            },
            "pdu3InputTotalEnergy": {
                'unit_of_measurement': Sensor.UNIT_WATTHOURS,
                'name': 'Total Input Energy usage',
                'scale': Sensor.SCALE_KILO,
            },
            "pdu3InputPowerFactor": {
                'unit_of_measurement': Sensor.UNIT_PERCENT,
                'name': 'Total Input Power Factor',
            },
            "pdu3InputPowerVAR": {
                'unit_of_measurement': Sensor.UNIT_VAR,
                'name': 'Total Input Reactive Power',
            },
        }
    },
    {
        'extra_columns': ['pdu3TemperatureProbeStatus'],
        'filter': lambda x: x.get('pdu3TemperatureProbeStatus') == 'connected',
        'sensors': {
            'pdu3TemperatureValue': {
                # Get from pdu3TemperatureScale to support F
                'unit_of_measurement': Sensor.UNIT_CELSIUS,
                'name': '{pdu3TemperatureName} Temperature',
                'precision': 1,
            },
        },
    },
    {
        'extra_columns': ['pdu3HumidityProbeStatus'],
        'filter': lambda x: x.get('pdu3HumidityProbeStatus') == 'connected',
        'sensors': {
            'pdu3HumidityValue': {
                'unit_of_measurement': Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY,
                'name': '{pdu3HumidityName} Humidity',
                'precision': 1,
            },
        },
    },
]


class CPQPowerMib(mibretriever.MibRetriever):
    """Custom class for retrieveing sensors from APC UPSes."""

    mib = get_mib('CPQPOWER-MIB')

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Gets all the interesting sensors for this device."""
        names = yield self._get_names()
        result = []
        for config in SENSORS:
            r = yield self._get_sensors(names, **config)
            result.extend(r)
        return result

    def _get_oid(self, column, index):
        return self.mib['nodes'][column]['oid'] + index

    @defer.inlineCallbacks
    def _get_names(self):
        result = {}
        names = yield self.retrieve_columns(['pdu3Name'])
        names = reduce_index(names)
        for index, row in names.items():
            name = row.get('pdu3Name')
            if name is None:
                name = ''
            name = name.strip()
            name = name.replace('\0', '')
            result[index] = name
        return result

    @defer.inlineCallbacks
    def _get_sensors(self, names, sensors, extra_columns=None, filter=lambda x: True):
        if extra_columns is None:
            extra_columns = []
        entries = yield self.retrieve_columns(extra_columns + list(sensors.keys()))
        entries = self.translate_result(entries)

        result = []
        for index, row in entries.items():
            if not filter(row):
                continue
            result.extend(self._mksensors(index, row, sensors, names))
        return result

    def _mksensors(self, index, row, table, names):
        result = []
        for col, config in table.items():
            if row.get(col) < 0:
                continue
            sensor = dict(
                oid=self._get_oid(col, index),
                internal_name='{}{}'.format(col, index),
                mib=self.get_module_name(),
            )
            for key, value in config.items():
                if callable(value):
                    value = value(row)
                elif isinstance(value, str):
                    value = value.format(**row)
                sensor[key] = value
            name = names.get(index[0])
            if name:
                sensor['name'] = "{} {}".format(name, sensor['name'])
            if 'description' not in sensor:
                sensor['description'] = sensor['name']
            result.append(sensor)
        return result

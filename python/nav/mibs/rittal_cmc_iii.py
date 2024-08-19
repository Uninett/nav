#
# Copyright (C) 2017 Uninett AS
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
"""A class for getting sensor readings from Rittal CMC III devices"""

from collections import defaultdict
import math

from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

DEGREES_CELSIUS = "\xb0C"
DEGREES_FAHRENHEIT = "\xb0F"
UNIT_MAP = {
    DEGREES_CELSIUS: Sensor.UNIT_CELSIUS,
    DEGREES_FAHRENHEIT: Sensor.UNIT_FAHRENHEIT,
    'mA': Sensor.UNIT_AMPERES,
    'A': Sensor.UNIT_AMPERES,
    'W': Sensor.UNIT_WATTS,
    'V': Sensor.UNIT_VOLTS_DC,
    's': Sensor.UNIT_SECONDS,
    'l/min': Sensor.UNIT_LPM,
    '%': Sensor.UNIT_PERCENT,
    '': Sensor.UNIT_UNKNOWN,
    'VA': Sensor.UNIT_VOLTAMPERES,
    'var': Sensor.UNIT_VAR,
    'kWh': Sensor.UNIT_WATTHOURS,
    'kVAh': Sensor.UNIT_VOLTAMPEREHOURS,
    'Hz': Sensor.UNIT_HERTZ,
}

UNIT_SCALE = {
    'mA': 'milli',
    'kWh': 'kilo',
    'kVAh': 'kilo',
}

SENSOR_COLUMNS = [
    'cmcIIIVarType',
    'cmcIIIVarName',
    'cmcIIIVarUnit',
    'cmcIIIVarDatatype',
    'cmcIIIVarScale',
    'cmcIIIVarValueStr',
]

IGNORED_STATUSES = {
    'n.a.',
    'Inactive',
}


class RittalCMCIIIMib(MibRetriever):
    """MibRetriever for Rittal CMC III devices"""

    mib = get_mib('RITTAL-CMC-III-MIB')

    def get_module_name(self):
        """Returns the MIB module name"""
        return self.mib.get('moduleName', None)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Discovers and returns all eligible sensors from the device."""
        devices = yield self.get_devices()
        sensors = yield self.get_sensors(devices)
        return sensors

    @defer.inlineCallbacks
    def get_devices(self):
        devices = yield self.retrieve_columns(
            ['cmcIIIDevName', 'cmcIIIDevAlias', 'cmcIIIDevNumberOfVars']
        )
        devices = self.translate_result(devices)
        return devices

    @defer.inlineCallbacks
    def get_sensors(self, devices):
        dev_names = {oid: dev['cmcIIIDevName'] for oid, dev in devices.items()}
        dev_aliases = {oid: dev['cmcIIIDevAlias'] for oid, dev in devices.items()}
        sensors = yield self.retrieve_columns(SENSOR_COLUMNS)
        sensors = self.translate_result(sensors)
        result = []
        mapping = defaultdict(dict)
        for oid, values in sensors.items():
            name = values['cmcIIIVarName']
            name_parts = name.split(".")
            suffix = name_parts[-1]
            sensor = ".".join(name_parts[:-1])
            mapping[sensor][suffix] = values
        for sname, data in mapping.items():
            description = data.get('DescName', {}).get('cmcIIIVarValueStr', sname)
            status = data.get('Status', {}).get('cmcIIIVarValueStr', 'OK')
            if status in IGNORED_STATUSES:
                self._logger.debug('Ignoring sensor %s due to status %s', sname, status)
                continue
            for var_name, values in data.items():
                oid = values[0]
                if values['cmcIIIVarType'] != 'value':
                    continue
                if values['cmcIIIVarDatatype'] != 'int':
                    self._logger.warning(
                        "Found sensor %s with datatype %s",
                        values['cmcIIIVarName'],
                        values['cmcIIIVarDatatype'],
                    )
                    continue
                raw_unit = values['cmcIIIVarUnit']
                scale = UNIT_SCALE.get(raw_unit, None)
                unit = UNIT_MAP.get(raw_unit, raw_unit)
                name = values['cmcIIIVarName']
                raw_precision = values['cmcIIIVarScale']
                if raw_precision < 0:
                    precision = math.log10(-raw_precision)
                elif raw_precision == 0:
                    precision = 0
                else:
                    precision = -math.log10(raw_precision)
                var_descr = '{}: {}'.format(dev_aliases[oid[:-1]], description)
                if var_name != 'Value':
                    var_descr += " {}".format(var_name)
                sensor = dict(
                    oid=str(self.nodes['cmcIIIVarValueInt'].oid + oid),
                    unit_of_measurement=unit,
                    precision=precision,
                    scale=scale,
                    description=var_descr,
                    name=name,
                    internal_name='{dev}_{var}'.format(
                        dev=dev_names[oid[:-1]], var=name
                    ),
                    mib=self.get_module_name(),
                )
                result.append(sensor)
        return result

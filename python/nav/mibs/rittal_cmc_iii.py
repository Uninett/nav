#
# Copyright (C) 2017 UNINETT
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
"""A class for getting sensor readings from Rittal CMC III devices"""

import math

from twisted.internet import defer
from twisted.internet.defer import returnValue
from nav.mibs.mibretriever import MibRetriever

DEGREES_CELSIUS = "\xb0C"
DEGREES_FAHRENHEIT = "\xb0F"
UNIT_MAP = {
    DEGREES_CELSIUS: "Celsius",
    DEGREES_FAHRENHEIT: "Fahrenheit",
    'mA': 'ampere',
}

UNIT_SCALE = {
    'mA': 'milli',
}

SENSOR_COLUMNS = [
    'cmcIIIVarType',
    'cmcIIIVarName',
    'cmcIIIVarUnit',
    'cmcIIIVarDatatype',
    'cmcIIIVarScale',
    'cmcIIIVarValueStr',
]


class RittalCMCIIIMib(MibRetriever):
    """MibRetriever for Rittal CMC III devices"""
    from nav.smidumps.rittal_cmc_iii_mib import MIB as mib

    def get_module_name(self):
        """Returns the MIB module name"""
        return self.mib.get('moduleName', None)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Discovers and returns all eligible sensors from the device.
        """
        devices = yield self.get_devices()
        sensors = yield self.get_sensors(devices)
        returnValue(sensors)

    @defer.inlineCallbacks
    def get_devices(self):
        devices = yield self.retrieve_columns(['cmcIIIDevName',
                                               'cmcIIIDevNumberOfVars'])
        devices = self.translate_result(devices)
        returnValue(devices)

    @defer.inlineCallbacks
    def get_sensors(self, devices):
        dev_names = {oid: dev['cmcIIIDevName'] for oid, dev in devices.items()}
        sensors = yield self.retrieve_columns(SENSOR_COLUMNS)
        sensors = self.translate_result(sensors)
        result = []
        for oid, values in sensors.items():
            if values['cmcIIIVarType'] != 'value':
                continue
            if values['cmcIIIVarDatatype'] != 'int':
                self._logger.warning("Found sensor %s with datatype %s",
                                     values['cmcIIIVarName'],
                                     values['cmcIIIVarDatatype'])
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
            sensor = dict(
                oid=str(self.nodes['cmcIIIVarValueInt'].oid + oid),
                unit_of_measurement=unit,
                precision=precision,
                scale=scale,
                description=name,
                name=name,
                internal_name='{dev}_{var}'.format(
                    dev=dev_names[oid[:-1]],
                    var=name),
                mib=self.get_module_name(),
            )
            result.append(sensor)
        returnValue(result)

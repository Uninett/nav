#
# Copyright (C) 2019 Uninett AS
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
"""A class for getting DOM values from Coriant Groove equipment"""

from twisted.internet import defer
from twisted.internet.defer import returnValue
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

UNIT_DECIBEL = "dB"  # This is actually not defined in Sensor
UNIT_PS = "ps"
UNIT_PS_PER_NM = "ps/nm"

OPTICAL_CHANNEL_COLUMNS = {
    "ochOsActualTxOpticalPower": {
        "unit_of_measurement": Sensor.UNIT_DBM,
        "type": "string",
        "name": "{port} TX Optical Power",
    },
    "ochOsActualFrequency": {
        "unit_of_measurement": Sensor.UNIT_HERTZ,
        "scale": Sensor.SCALE_MEGA,
        "type": "string",
        "name": "{port} actual laser frequency",
    },
    "ochOsFrequency": {
        "unit_of_measurement": Sensor.UNIT_HERTZ,
        "scale": Sensor.SCALE_MEGA,
        "type": "string",
        "name": "{port} laser frequency",
    },
    "ochOsRequiredTxOpticalPower": {
        "unit_of_measurement": Sensor.UNIT_DBM,
        "type": "string",
        "name": "{port} required TX Optical Power",
    },
    "ochOsRxAttenuation": {
        "unit_of_measurement": UNIT_DECIBEL,
        "type": "string",
        "name": "{port} RX attenuation",
    },
    "ochOsTxFilterRollOff": {
        "unit_of_measurement": Sensor.UNIT_OTHER,
        "type": "string",
        "name": "{port} TX filter roll off",
    },
    "ochOsPreemphasisValue": {
        "unit_of_measurement": Sensor.UNIT_OTHER,
        "type": "string",
        "name": "{port} Preemphasis",
    },
    "ochOsDGD": {
        "unit_of_measurement": Sensor.UNIT_SECONDS,
        "scale": Sensor.SCALE_PICO,
        "name": "{port} differential group delay",
    },
    "ochOsCD": {
        "unit_of_measurement": UNIT_PS_PER_NM,
        "name": "{port} chromatic dispersion",
    },
    "ochOsOSNR": {
        "unit_of_measurement": UNIT_DECIBEL,
        "type": "string",
        "name": "{port} OSNR",
    },
    "ochOsQFactor": {
        "unit_of_measurement": UNIT_DECIBEL,
        "type": "string",
        "name": "{port} Q-factor",
    },
    "ochOsPreFecBer": {
        "unit_of_measurement": Sensor.UNIT_OTHER,
        "type": "string",
        "name": "{port} PreFEC bit error ratio",
    },
}


class CoriantGrooveMib(MibRetriever):
    """MibRetriever for Coriant Groove DOM Sensors"""

    mib = get_mib("CORIANT-GROOVE-MIB")

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Discovers and returns all eligible optical channel sensors"""
        sensors = yield self.get_optical_channel_sensors()
        returnValue(sensors)

    @defer.inlineCallbacks
    def get_optical_channel_sensors(self):
        """Returns sensor definitions for the optical channel measurements that were found"""
        column_names = ["ochOsAliasName"] + list(OPTICAL_CHANNEL_COLUMNS.keys())
        response = yield self.retrieve_columns(column_names)
        self._logger.debug("Found ochOsTable columns: %r", response)

        sensors = []
        for row, columns in response.items():
            alias = columns.get("ochOsAliasName", str(row))
            sensors.extend(
                [
                    self._make_och_sensor(index=row, port=alias, column=column)
                    for column in OPTICAL_CHANNEL_COLUMNS
                    if column in columns
                ]
            )
        self._logger.debug("Returning sensor list: %r", sensors)
        returnValue(sensors)

    def _make_och_sensor(self, index, port, column):
        value_oid = self.nodes[column].oid
        config = OPTICAL_CHANNEL_COLUMNS.get(column)
        sensor = dict(
            oid=str(value_oid + index),
            scale=None,
            mib=self.get_module_name(),
            internal_name="{port}.{column}".format(port=port, column=column),
            description="{port}: " + self._get_sensor_description(column),
        )
        sensor.update(config)
        sensor["name"] = sensor["name"].format(port=port)
        sensor["description"] = sensor["description"].format(port=port)
        return sensor

    def _get_sensor_description(self, column):
        """Returns the first line of the mib object's description"""
        mib_object = self.nodes[column].raw_mib_data
        description = mib_object.get("description", "").strip()
        return description.split("\n")[0]

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
"""A class for getting DOM values for juniper equipment

"""

from twisted.internet import defer
from twisted.internet.defer import returnValue
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

COLUMNS = {
    "jnxDomCurrentRxLaserPower": {
        "unit_of_measurement": Sensor.UNIT_DBM,
        "precision": 2,
        "name": "{ifc} RX Laser Power",
        "description": "{ifc} RX Laser Power",
    },
    "jnxDomCurrentTxLaserBiasCurrent": {
        "unit_of_measurement": Sensor.UNIT_AMPERES,
        "precision": 3,
        "scale": Sensor.SCALE_MILLI,
        "name": "{ifc} TX Laser Bias Current",
        "description": "{ifc} TX Laser Bias Current",
    },
    "jnxDomCurrentTxLaserOutputPower": {
        "unit_of_measurement": Sensor.UNIT_DBM,
        "precision": 2,
        "name": "{ifc} TX Laser Output Power",
        "description": "{ifc} TX Laser Output Power",
    },
    "jnxDomCurrentModuleTemperature": {
        "unit_of_measurement": Sensor.UNIT_CELSIUS,
        "precision": 0,
        "name": "{ifc} Module Temperature",
        "description": "{ifc} Module Temperature",
    },
}

THRESHOLD_COLUMNS = {
    "jnxDomCurrentRxLaserPower": [
        "jnxDomCurrentRxLaserPowerHighAlarmThreshold",
        "jnxDomCurrentRxLaserPowerLowAlarmThreshold",
        "jnxDomCurrentRxLaserPowerHighWarningThreshold",
        "jnxDomCurrentRxLaserPowerLowWarningThreshold",
    ],
    "jnxDomCurrentTxLaserBiasCurrent": [
        "jnxDomCurrentTxLaserBiasCurrentHighAlarmThreshold",
        "jnxDomCurrentTxLaserBiasCurrentLowAlarmThreshold",
        "jnxDomCurrentTxLaserBiasCurrentHighWarningThreshold",
        "jnxDomCurrentTxLaserBiasCurrentLowWarningThreshold",
    ],
    "jnxDomCurrentTxLaserOutputPower": [
        "jnxDomCurrentTxLaserOutputPowerHighAlarmThreshold",
        "jnxDomCurrentTxLaserOutputPowerLowAlarmThreshold",
        "jnxDomCurrentTxLaserOutputPowerHighWarningThreshold",
        "jnxDomCurrentTxLaserOutputPowerLowWarningThreshold",
    ],
    "jnxDomCurrentModuleTemperature": [
        "jnxDomCurrentModuleTemperatureHighAlarmThreshold",
        "jnxDomCurrentModuleTemperatureLowAlarmThreshold",
        "jnxDomCurrentModuleTemperatureHighWarningThreshold",
        "jnxDomCurrentModuleTemperatureLowWarningThreshold",
    ],
}


class JuniperDomMib(MibRetriever):
    """MibRetriever for Juniper DOM Sensors"""

    mib = get_mib('JUNIPER-DOM-MIB')

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Discovers and returns all eligible dom sensors from this
        device.
        """
        sensors = []
        for column, config in COLUMNS.items():
            sensors += yield self.handle_sensor_column(column, config)
        returnValue(sensors)

    @defer.inlineCallbacks
    def handle_sensor_column(self, column, config):
        """Returns the sensors of the given type"""
        result = []
        value_oid = self.nodes[column].oid
        rows = yield self.retrieve_column(column)
        for row in rows:
            sensor = dict(
                oid=str(value_oid + row),
                scale=None,
                mib=self.get_module_name(),
                internal_name="{ifc}." + column,
                ifindex=row[-1],
            )
            sensor.update(config)
            result.append(sensor)
        returnValue(result)

    @defer.inlineCallbacks
    def get_all_thresholds(self):
        thresholds = []
        for sensor_column, threshold_columns in THRESHOLD_COLUMNS.items():
            sensor_oid = self.nodes[sensor_column].oid
            for threshold_column in threshold_columns:
                thresholds += yield self.handle_threshold_column(
                    threshold_column, sensor_oid
                )
        returnValue(thresholds)

    @defer.inlineCallbacks
    def handle_threshold_column(self, column, sensor_oid):
        """Returns the sensor thresholds of the given type"""
        result = []
        value_oid = self.nodes[column].oid
        rows = yield self.retrieve_column(column)
        for row, value in rows.items():
            threshold = dict(
                oid=str(value_oid + row),
                mib=self.get_module_name(),
                name=column,
                value=value,
                sensor_oid=str(sensor_oid + row),
            )
            result.append(threshold)
        returnValue(result)

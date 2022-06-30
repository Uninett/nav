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

SENSOR_COLUMNS = {
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
    "jnxDomCurrentRxLaserPower": {
        "high_alarm_threshold": "jnxDomCurrentRxLaserPowerHighAlarmThreshold",
        "low_alarm_threshold": "jnxDomCurrentRxLaserPowerLowAlarmThreshold",
        "high_warning_threshold": "jnxDomCurrentRxLaserPowerHighWarningThreshold",
        "low_warning_threshold": "jnxDomCurrentRxLaserPowerLowWarningThreshold",
    },
    "jnxDomCurrentTxLaserBiasCurrent": {
        "high_alarm_threshold": "jnxDomCurrentTxLaserBiasCurrentHighAlarmThreshold",
        "low_alarm_threshold": "jnxDomCurrentTxLaserBiasCurrentLowAlarmThreshold",
        "high_warning_threshold": "jnxDomCurrentTxLaserBiasCurrentHighWarningThreshold",
        "low_warning_threshold": "jnxDomCurrentTxLaserBiasCurrentLowWarningThreshold",
    },
    "jnxDomCurrentTxLaserOutputPower": {
        "high_alarm_threshold": "jnxDomCurrentTxLaserOutputPowerHighAlarmThreshold",
        "low_alarm_threshold": "jnxDomCurrentTxLaserOutputPowerLowAlarmThreshold",
        "high_warning_threshold": "jnxDomCurrentTxLaserOutputPowerHighWarningThreshold",
        "low_warning_threshold": "jnxDomCurrentTxLaserOutputPowerLowWarningThreshold",
    },
    "jnxDomCurrentModuleTemperature": {
        "high_alarm_threshold": "jnxDomCurrentModuleTemperatureHighAlarmThreshold",
        "low_alarm_threshold": "jnxDomCurrentModuleTemperatureLowAlarmThreshold",
        "high_warning_threshold": "jnxDomCurrentModuleTemperatureHighWarningThreshold",
        "low_warning_threshold": "jnxDomCurrentModuleTemperatureLowWarningThreshold",
    },
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
        for column, config in SENSOR_COLUMNS.items():
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
        for sensor_column, thresholds in THRESHOLD_COLUMNS.items():
            sensor_oid = self.nodes[sensor_column].oid
            for threshold_name, threshold_column in thresholds.items():
                thresholds += yield self.handle_threshold_column(
                    threshold_column, threshold_name, sensor_oid
                )
        returnValue(thresholds)

    @defer.inlineCallbacks
    def handle_threshold_column(self, column, name, sensor_oid):
        """Returns the sensor thresholds of the given type"""
        result = []
        value_oid = self.nodes[column].oid
        rows = yield self.retrieve_column(column)
        for row, value in rows.items():
            threshold = dict(
                oid=str(value_oid + row),
                mib=self.get_module_name(),
                name=name,
                value=value,
                sensor_oid=str(sensor_oid + row),
            )
            result.append(threshold)
        returnValue(result)

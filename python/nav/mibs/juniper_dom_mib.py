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
        "jnxDomCurrentRxLaserPowerHighAlarmThreshold": {
            "name": "{ifc} RX Laser Power High Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentRxLaserPowerLowAlarmThreshold": {
            "name": "{ifc} RX Laser Power Low Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentRxLaserPowerHighWarningThreshold": {
            "name": "{ifc} RX Laser Power High Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
        "jnxDomCurrentRxLaserPowerLowWarningThreshold": {
            "name": "{ifc} RX Laser Power Low Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
    },
    "jnxDomCurrentTxLaserBiasCurrent": {
        "jnxDomCurrentTxLaserBiasCurrentHighAlarmThreshold": {
            "name": "{ifc} TX Laser Bias Current High Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentTxLaserBiasCurrentLowAlarmThreshold": {
            "name": "{ifc} TX Laser Bias Current Low Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentTxLaserBiasCurrentHighWarningThreshold": {
            "name": "{ifc} TX Laser Bias Current High Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
        "jnxDomCurrentTxLaserBiasCurrentLowWarningThreshold": {
            "name": "{ifc} TX Laser Bias Current Low Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
    },
    "jnxDomCurrentTxLaserOutputPower": {
        "jnxDomCurrentTxLaserOutputPowerHighAlarmThreshold": {
            "name": "{ifc} TX Laser Output Power High Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentTxLaserOutputPowerLowAlarmThreshold": {
            "name": "{ifc} TX Laser Output Power Low Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentTxLaserOutputPowerHighWarningThreshold": {
            "name": "{ifc} TX Laser Output Power High Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
        "jnxDomCurrentTxLaserOutputPowerLowWarningThreshold": {
            "name": "{ifc} TX Laser Output Power Low Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
    },
    "jnxDomCurrentModuleTemperature": {
        "jnxDomCurrentModuleTemperatureHighAlarmThreshold": {
            "name": "{ifc} Module Temperature High Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentModuleTemperatureLowAlarmThreshold": {
            "name": "{ifc} Module Temperature Low Alarm Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
        },
        "jnxDomCurrentModuleTemperatureHighWarningThreshold": {
            "name": "{ifc} Module Temperature High Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
        "jnxDomCurrentModuleTemperatureLowWarningThreshold": {
            "name": "{ifc} Module Temperature Low Warning Threshold",
            "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
            "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
        },
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
        for sensor_column, sensor_config in SENSOR_COLUMNS.items():
            sensors += yield self.handle_sensor_column(sensor_column, sensor_config)
            for threshold_column, threshold_config in THRESHOLD_COLUMNS[sensor_column]:
                sensors += yield self.handle_threshold_column(
                    threshold_column,
                    threshold_config,
                    sensor_column,
                    sensor_config,
                )
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
    def handle_threshold_column(
        self, column, config, related_sensor_column, related_sensor_config
    ):
        """Returns the sensor thresholds of the given type"""
        result = []
        value_oid = self.nodes[column].oid
        related_sensor_oid = self.nodes[related_sensor_column].oid
        rows = yield self.retrieve_column(column)
        for row, value in rows.items():
            threshold_sensor = dict(
                oid=str(value_oid + row),
                scale=None,
                mib=self.get_module_name(),
                description=config['name'],
                internal_name="{ifc}." + column,
                ifindex=row[-1],
                unit_of_measurement=related_sensor_config['unit_of_measurement'],
                precision=related_sensor_config['precision'],
                threshold_for_oid=str(related_sensor_oid + row),
            )
            threshold_sensor.update(config)
            result.append(threshold_sensor)
        returnValue(result)

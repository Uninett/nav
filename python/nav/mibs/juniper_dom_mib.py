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
"""A class for getting DOM values for juniper equipment"""

from twisted.internet import defer
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

THRESHOLD_LEVELS = {
    "HighAlarm": {
        "label": "High Alarm",
        "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
        "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
    },
    "LowAlarm": {
        "label": "Low Alarm",
        "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
        "threshold_alert_type": Sensor.ALERT_TYPE_ALERT,
    },
    "HighWarning": {
        "label": "High Warning",
        "threshold_type": Sensor.THRESHOLD_TYPE_HIGH,
        "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
    },
    "LowWarning": {
        "label": "Low Warning",
        "threshold_type": Sensor.THRESHOLD_TYPE_LOW,
        "threshold_alert_type": Sensor.ALERT_TYPE_WARNING,
    },
}

THRESHOLD_COLUMNS = {
    sensor_column: {
        f"{sensor_column}{level}Threshold": {
            "name": f"{config['name']} {attrs['label']} Threshold",
            "threshold_type": attrs["threshold_type"],
            "threshold_alert_type": attrs["threshold_alert_type"],
        }
        for level, attrs in THRESHOLD_LEVELS.items()
    }
    for sensor_column, config in SENSOR_COLUMNS.items()
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
            for threshold_column, threshold_config in THRESHOLD_COLUMNS[
                sensor_column
            ].items():
                sensors += yield self.handle_threshold_column(
                    threshold_column,
                    threshold_config,
                    sensor_column,
                    sensor_config,
                )
        return sensors

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
        return result

    @defer.inlineCallbacks
    def handle_threshold_column(
        self, column, config, related_sensor_column, related_sensor_config
    ):
        """Returns the sensor thresholds of the given type"""
        result = []
        value_oid = self.nodes[column].oid
        related_sensor_oid = self.nodes[related_sensor_column].oid
        rows = yield self.retrieve_column(column)
        for row in rows:
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
        return result

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
"""A class for getting sensor information from Raritan PDU2 devices
"""

from twisted.internet import defer
from twisted.internet.defer import returnValue
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

UNIT_MAP = {
    'none': Sensor.UNIT_UNKNOWN,
    'other': Sensor.UNIT_OTHER,
    'volt': Sensor.UNIT_VOLTS_AC,
    'amp': Sensor.UNIT_AMPERES,
    'watt': Sensor.UNIT_WATTS,
    'voltamp': Sensor.UNIT_VOLTAMPERES,
    'wattHour': Sensor.UNIT_WATTHOURS,
    'voltampHour': Sensor.UNIT_VOLTAMPEREHOURS,
    'degreeC': Sensor.UNIT_CELSIUS,
    'hertz': Sensor.UNIT_HERTZ,
    'percent': Sensor.UNIT_PERCENT,
    'meterpersec': Sensor.UNIT_MPS,
    'pascal': Sensor.UNIT_PASCAL,
    'psi': Sensor.UNIT_PSI,
    'g': Sensor.UNIT_GRAMS,
    'degreeF': Sensor.UNIT_FAHRENHEIT,
    'feet': Sensor.UNIT_FEET,
    'inches': Sensor.UNIT_INCHES,
    'cm': Sensor.UNIT_METERS,
    'meters': Sensor.UNIT_METERS,
    'rpm': Sensor.UNIT_RPM,
    'degrees': Sensor.UNIT_DEGREES,
    'lux': Sensor.UNIT_LUX,
    'grampercubicmeter': Sensor.UNIT_GPCM,
    'var': Sensor.UNIT_UNKNOWN,
}

UNIT_SCALE = {
    'cm': -2,
}

SENSOR_COLUMNS = [
    "{table}Units",
    "{table}DecimalDigits",
    "{table}Maximum",
    "{table}Minimum",
]


class PDU2Mib(MibRetriever):
    """MibRetriever for Raritan PDU2"""
    mib = get_mib('PDU2-MIB')

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Discovers and returns all eligible sensors.
        """
        result = []
        sensors, inlets = yield self.get_inlet_sensors()
        result += sensors
        result += yield self.get_inlet_pole_sensors(inlets)
        result += yield self.get_over_current_protection_sensors()
        returnValue(result)

    def retrieve_sensor_columns(self, table):
        columns = [fmt.format(table=table) for fmt in SENSOR_COLUMNS]
        return self.retrieve_columns(columns)

    def get_sensor(self, table, index, row, name, description, internal_name):
        unit = row['{table}Units'.format(table=table)]
        scale = UNIT_SCALE.get(unit, 0)
        unit = UNIT_MAP.get(unit, unit)
        captable = table.replace(table[0], table[0].capitalize(), 1)
        value_oid = self.nodes['measurements{table}Value'.format(
            table=captable)].oid
        precision = row['{table}DecimalDigits'.format(table=table)] + scale
        minimum = row['{table}Minimum'.format(table=table)] / (10.**precision)
        maximum = row['{table}Maximum'.format(table=table)]
        if maximum == 4294967295:
            maximum = None
        else:
            maximum = maximum / (10.**precision)
        sensor = dict(
            oid=str(value_oid + index),
            unit_of_measurement=unit,
            precision=precision,
            scale=None,
            description=description,
            name=name,
            internal_name=internal_name,
            mib=self.get_module_name(),
            minimum=minimum,
            maximum=maximum,
        )
        return sensor

    @defer.inlineCallbacks
    def get_inlet_sensors(self):
        """Discovers and returns sensors from the inletSensorConfigurationTable.
        """
        result = []
        table = 'inletSensor'
        inlets = yield self.retrieve_column('inletLabel')
        channels = yield self.retrieve_sensor_columns(table)
        channels = self.translate_result(channels)
        for index, row in channels.items():
            pdu_id, inlet_id, sensor_type = index
            inlet = inlets.get(index[:2], inlet_id)
            sensor_type = self.nodes['sensorType'].to_python(sensor_type)
            name = "pdu {pdu} inlet {inlet} {sensor}".format(
                pdu=pdu_id, inlet=inlet, sensor=sensor_type)
            internal_name = "pdu{pdu}_{inlet}_{sensor}".format(
                pdu=pdu_id, inlet=inlet, sensor=sensor_type)
            sensor = self.get_sensor(table, index, row, name, name,
                                     internal_name)
            result.append(sensor)
        returnValue((result, inlets))

    @defer.inlineCallbacks
    def get_inlet_pole_sensors(self, inlets):
        """Discovers and returns sensors from the inletPoleSensorConfigurationTable.
        """
        result = []
        table = 'inletPoleSensor'
        channels = yield self.retrieve_sensor_columns(table)
        channels = self.translate_result(channels)
        pole_lines = yield self.retrieve_column('inletPoleLine')
        pole_lines = {index: self.nodes['inletPoleLine'].to_python(value)
                      for index, value in pole_lines.items()}
        for index, row in channels.items():
            pdu_id, inlet_id, inlet_pole_index, sensor_type = index
            inlet = inlets.get(index[:2], inlet_id)
            sensor_type = self.nodes['sensorType'].to_python(sensor_type)
            pole_line = pole_lines.get(index[:3],
                                       "Unknown lines %s" % inlet_pole_index)
            name = "pdu {pdu} inlet {inlet} {pole} {sensor}".format(
                pdu=pdu_id, inlet=inlet, sensor=sensor_type,
                pole=pole_line)
            internal_name = "pdu{pdu}_{inlet}_{line}_{sensor}".format(
                pdu=pdu_id,
                inlet=inlet,
                line=pole_line,
                sensor=sensor_type)
            sensor = self.get_sensor(table, index, row, name, name,
                                     internal_name)
            result.append(sensor)
        returnValue(result)

    @defer.inlineCallbacks
    def get_over_current_protection_sensors(self):
        """Discovers and returns sensors from the
           overCurrentProtectorSensorConfigurationTable.
        """
        result = []
        table = 'overCurrentProtectorSensor'
        channels = yield self.retrieve_sensor_columns(table)
        channels = self.translate_result(channels)
        labels = yield self.retrieve_column('overCurrentProtectorLabel')
        for index, row in channels.items():
            pdu_id, protector_index, sensor_type = index
            sensor_type = self.nodes['sensorType'].to_python(sensor_type)
            label = labels.get(index[:2],
                               "unlabeled protector {}".format(
                                   protector_index))
            name = "pdu {pdu} overCurrentProtector {protector} {sensor}".format(
                pdu=pdu_id, protector=label, sensor=sensor_type)
            internal_name = "pdu{pdu}_ocp{label}_{sensor}".format(
                pdu=pdu_id, label=label, sensor=sensor_type)
            sensor = self.get_sensor(table, index, row, name, name,
                                     internal_name)
            if sensor_type == 'trip':
                sensor['unit_of_measurement'] = 'boolean'
            result.append(sensor)
        returnValue(result)

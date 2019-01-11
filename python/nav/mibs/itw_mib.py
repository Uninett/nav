# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
#
"""
A class that tries to retrieve all sensors from WeatherGoose I.

Uses the vendor-specifica IT-WATCHDOGS-MIB to detect and collect
sensor-information.
"""
from django.utils.six import itervalues
from twisted.internet import defer
from django.utils import six

from nav.mibs import reduce_index
from nav.mibs import mibretriever
from nav.models.manage import Sensor
from nav.oids import OID


def for_table(table_name):
    """Used for annotating functions to process the returned
    tables"""
    if not hasattr(for_table, 'map'):
        for_table.map = {}

    def decorate(method):
        """Setup link between table and function"""
        name = method.func_name if six.PY2 else method.__name__
        for_table.map[table_name] = name
        return method

    return decorate


class ItWatchDogsMib(mibretriever.MibRetriever):
    """A class that tries to retrieve all sensors from WeatherGoose I"""
    from nav.smidumps.itw_mib import MIB as mib

    oid_name_map = dict((OID(attrs['oid']), name)
                        for name, attrs in mib['nodes'].items())
    lowercase_nodes = dict((key.lower(), key)
                           for key in mib['nodes'])

    def _get_oid_for_sensor(self, sensor_name):
        """Return the OID for the given sensor-name as a string; Return
        None if sensor-name is not found.
        """
        oid_str = None
        nodes = self.mib.get('nodes', None)
        if nodes:
            sensor_def = nodes.get(sensor_name, None)
            if sensor_def:
                oid_str = sensor_def.get('oid', None)
        return oid_str

    def _make_result_dict(self, sensor_oid, base_oid, serial, desc,
                          u_o_m=None, precision=0, scale=None, name=None):
        """ Make a simple dictionary to return to plugin"""
        if not sensor_oid or not base_oid or not serial or not desc:
            return {}
        oid = OID(base_oid) + OID(sensor_oid)
        internal_name = serial + desc
        return {'oid': str(oid),
                'unit_of_measurement': u_o_m,
                'precision': precision,
                'scale': scale,
                'description': desc,
                'name': name,
                'internal_name': internal_name,
                'mib': self.get_module_name(),
                }

    @for_table('climateTable')
    def _get_climate_sensors_params(self, climate_sensors):
        """ Collect all climate sensors and corresponding parameters"""
        sensors = []
        for climate_sensor in itervalues(climate_sensors):
            available = climate_sensor.get('climateAvail', None)
            if available:
                climate_oid = climate_sensor.get(0, None)
                serial = climate_sensor.get('climateSerial', None)
                name = climate_sensor.get('climateName', None)

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateTempC'),
                    serial, 'climateTempC',
                    u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateHumidity'),
                    serial, 'climateHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY,
                    name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateAirflow'),
                    serial, 'climateAirflow', name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateLight'),
                    serial, 'climateLight', name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateSound'),
                    serial, 'climateSound', name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateIO1'),
                    serial, 'climateIO1', name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateIO2'),
                    serial, 'climateIO2', name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateIO3'),
                    serial, 'climateIO3', name=name))
        return sensors

    @for_table('tempSensorTable')
    def _get_temp_sensors_params(self, temp_sensors):
        """ Collect all temperature sensors and corresponding parameters"""
        sensors = []
        for temp_sensor in itervalues(temp_sensors):
            temp_sensor_avail = temp_sensor.get('tempSensorAvail', None)
            if temp_sensor_avail:
                temp_oid = temp_sensor.get(0, None)
                serial = temp_sensor.get('tempSensorSerial', 0)
                name = temp_sensor.get('tempSensorName', None)
                sensors.append(self._make_result_dict(
                    temp_oid,
                    self._get_oid_for_sensor('tempSensorTempC'),
                    serial, 'tempSensorTempC',
                    u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
        return sensors

    @for_table('airFlowSensorTable')
    def _get_airflow_sensors_params(self, airflow_sensors):
        """ Collect all airflow sensors and corresponding parameters"""
        sensors = []
        for airflow_sensor in itervalues(airflow_sensors):
            airflow_avail = airflow_sensor.get('airFlowSensorAvail', None)
            if airflow_avail:
                airflow_oid = airflow_sensor.get(0, None)
                serial = airflow_sensor.get('airFlowSensorSerial', None)
                name = airflow_sensor.get('airFlowSensorName', None)
                sensors.append(self._make_result_dict(
                    airflow_oid,
                    self._get_oid_for_sensor('airFlowSensorFlow'),
                    serial, 'airFlowSensorFlow',
                    name=name))

                sensors.append(self._make_result_dict(
                    airflow_oid,
                    self._get_oid_for_sensor('airFlowSensorTempC'),
                    serial, 'airFlowSensorTempC',
                    u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))

                sensors.append(self._make_result_dict(
                    airflow_oid,
                    self._get_oid_for_sensor('airFlowSensorHumidity'),
                    serial, 'airFlowSensorHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY,
                    name=name))
        return sensors

    @for_table('doorSensorTable')
    def _get_door_sensors_params(self, door_sensors):
        """ Collect all door sensors and corresponding parameters"""
        sensors = []
        for door_sensor in itervalues(door_sensors):
            door_avail = door_sensor.get('doorSensorAvail', None)
            if door_avail:
                door_oid = door_sensor.get(0, None)
                serial = door_sensor.get('doorSensorSerial', None)
                name = door_sensor.get('doorSensorName', None)
                sensors.append(self._make_result_dict(
                    door_oid,
                    self._get_oid_for_sensor('doorSensorStatus'),
                    serial, 'doorSensorStatus',
                    name=name))
        return sensors

    @for_table('waterSensorTable')
    def _get_water_sensors_params(self, water_sensors):
        """ Collect all water sensors and corresponding parameters"""
        sensors = []
        self._logger.debug('_get_water_sensors_params: %s' % water_sensors)
        for water_sensor in itervalues(water_sensors):
            water_avail = water_sensor.get('waterSensorAvail', 0)
            if water_avail:
                water_oid = water_sensor.get(0, None)
                serial = water_sensor.get('waterSensorSerial', None)
                name = water_sensor.get('waterSensorName', None)
                sensors.append(self._make_result_dict(water_oid,
                               self._get_oid_for_sensor('waterSensorDampness'),
                               serial, 'waterSensorDampness', name=name))
        return sensors

    @for_table('currentMonitorTable')
    def _get_current_sensors_params(self, current_sensors):
        sensors = []
        for current_sensor in itervalues(current_sensors):
            current_avail = current_sensor.get('currentMonitorAvail', None)
            if current_avail:
                current_oid = current_sensor.get(0, None)
                serial = current_sensor.get('currentMonitorSerial', None)
                name = current_sensor.get('currentMonitorName', None)
                sensors.append(self._make_result_dict(
                    current_oid,
                    self._get_oid_for_sensor('currentMonitorAmps'),
                    serial, 'currentMonitorAmps',
                    u_o_m=Sensor.UNIT_AMPERES, scale='milli',
                    name=name))
        return sensors

    @for_table('millivoltMonitorTable')
    def _get_millivolt_sensors_params(self, millivolt_sensors):
        sensors = []
        for millivolt_sensor in itervalues(millivolt_sensors):
            millivolt_avail = millivolt_sensor.get('millivoltMonitorAvail',
                                                   None)
            if millivolt_avail:
                millivolt_oid = millivolt_sensor.get(0, None)
                serial = millivolt_sensor.get('millivoltMonitorSerial', None)
                name = millivolt_sensor.get('millivoltMonitorName', None)
                sensors.append(self._make_result_dict(
                    millivolt_oid,
                    self._get_oid_for_sensor('millivoltMonitorMV'),
                    serial, 'millivoltMonitorMV',
                    u_o_m=Sensor.UNIT_VOLTS_DC,
                    scale='milli', name=name))
        return sensors

    @for_table('dewPointSensorTable')
    def _get_dewpoint_sensors_params(self, dewpoint_sensors):
        sensors = []
        for dewpoint_sensor in itervalues(dewpoint_sensors):
            dewpoint_avail = dewpoint_sensor.get('dewPointSensorAvail', None)
            if dewpoint_avail:
                dewpoint_oid = dewpoint_sensor.get(0, None)
                serial = dewpoint_sensor.get('dewPointSensorSerial', None)
                name = dewpoint_sensor.get('dewPointSensorName', None)
                sensors.append(self._make_result_dict(
                    dewpoint_oid,
                    self._get_oid_for_sensor('dewPointSensorDewPoint'),
                    serial, 'dewPointSensorDewPoint',
                    u_o_m=Sensor.UNIT_CELSIUS, name=name))

                sensors.append(self._make_result_dict(
                    dewpoint_oid,
                    self._get_oid_for_sensor('dewPointSensorTempC'),
                    serial, 'dewPointSensorTempC',
                    u_o_m=Sensor.UNIT_CELCIUS, name=name))

                sensors.append(self._make_result_dict(
                    dewpoint_oid,
                    self._get_oid_for_sensor('dewPointSensorHumidity'),
                    serial, 'dewPointSensorHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY, name=name))
        return sensors

    @for_table('digitalSensorTable')
    def _get_digital_sensors_params(self, digital_sensors):
        sensors = []
        for digital_sensor in itervalues(digital_sensors):
            digital_avail = digital_sensor.get('digitalSensorAvail', None)
            if digital_avail:
                digital_oid = digital_sensor.get(0, None)
                serial = digital_sensor.get('digitalSensorSerial', None)
                name = digital_sensor.get('digitalSensorName', None)
                sensors.append(self._make_result_dict(
                    digital_oid,
                    self._get_oid_for_sensor('digitalSensorDigital'),
                    serial, 'digitalSensorDigital', name=name))
        return sensors

    @for_table('cpmSensorTable')
    def _get_cpm_sensors_params(self, cpm_sensors):
        sensors = []
        for cpm_sensor in itervalues(cpm_sensors):
            cpm_avail = cpm_sensor.get('cpmSensorAvail', None)
            if cpm_avail:
                cpm_oid = cpm_sensor.get(0, None)
                serial = cpm_sensor.get('cpmSensorSerial', None)
                name = cpm_sensor.get('cpmSensorName', None)
                sensors.append(self._make_result_dict(
                    cpm_oid,
                    self._get_oid_for_sensor('cpmSensorStatus'),
                    serial, 'cpmSensorStatus', name=name))
        return sensors

    @for_table('smokeAlarmTable')
    def _get_smoke_sensors_params(self, smoke_sensors):
        sensors = []
        for smoke_sensor in itervalues(smoke_sensors):
            smoke_avail = smoke_sensor.get('smokeAlarmAvail', None)
            if smoke_avail:
                smoke_oid = smoke_sensor.get(0, None)
                serial = smoke_sensor.get('smokeAlarmSerial', None)
                name = smoke_sensor.get('smokeAlarmName', None)
                sensors.append(self._make_result_dict(
                    smoke_oid,
                    self._get_oid_for_sensor('smokeAlarmStatus'),
                    serial, 'smokeAlarmStatus',
                    name=name))
        return sensors

    @for_table('neg48VdcSensorTable')
    def _get_neg48vdc_sensors_params(self, neg48vdc_sensors):
        sensors = []
        for neg48vdc_sensor in itervalues(neg48vdc_sensors):
            neg48vdc_avail = neg48vdc_sensor.get('neg48VdcSensorAvail', None)
            if neg48vdc_avail:
                neg48vdc_oid = neg48vdc_sensor.get(0, None)
                serial = neg48vdc_sensor.get('neg48VdcSensorSerial', None)
                name = neg48vdc_sensor.get('neg48VdcSensorName', None)
                sensors.append(self._make_result_dict(
                    neg48vdc_oid,
                    self._get_oid_for_sensor('neg48VdcSensorVoltage'),
                    serial, 'neg48VdcSensorVoltage',
                    u_o_m=Sensor.UNIT_VOLTS_DC, name=name))
        return sensors

    @for_table('pos30VdcSensorTable')
    def _get_pos30vdc_sensors_params(self, pos30vdc_sensors):
        sensors = []
        for pos30vdc_sensor in itervalues(pos30vdc_sensors):
            pos30vdc_avail = pos30vdc_sensor.get('pos30VdcSensorAvail', None)
            if pos30vdc_avail:
                pos30vdc_oid = pos30vdc_sensor.get(0, None)
                serial = pos30vdc_sensor.get('pos30VdcSensorSerial', None)
                name = pos30vdc_sensor.get('pos30VdcSensorName', None)
                sensors.append(self._make_result_dict(
                    pos30vdc_oid,
                    self._get_oid_for_sensor('pos30VdcSensorVoltage'),
                    serial, 'pos30VdcSensorVoltage',
                    u_o_m=Sensor.UNIT_VOLTS_DC, name=name))
        return sensors

    @for_table('analogSensorTable')
    def _get_analog_sensors_params(self, analog_sensors):
        sensors = []
        for analog_sensor in itervalues(analog_sensors):
            analog_avail = analog_sensor.get('analogSensorAvail', None)
            if analog_avail:
                analog_oid = analog_sensor.get(0, None)
                serial = analog_sensor.get('analogSensorSerial', None)
                name = analog_sensor.get('analogSensorName', None)
                sensors.append(self._make_result_dict(
                    analog_oid,
                    self._get_oid_for_sensor('analogSensorAnalog'),
                    serial, 'analogSensorAnalog', name=name))
        return sensors

    @for_table("powerMonitorTable")
    def _get_power_monitor_params(self, power_monitors_sensors):
        sensors = []
        for pow_mon_sensor in itervalues(power_monitors_sensors):
            pow_mon_avail = pow_mon_sensor.get('powMonAvail', None)
            if pow_mon_avail:
                pow_mon_oid = pow_mon_sensor.get(0, None)
                serial = pow_mon_sensor.get('powMonSerial', None)
                name = pow_mon_sensor.get('powMonName', None)
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonKWattHrs'),
                    serial, 'powMonKWattHrs', u_o_m=Sensor.UNIT_WATTS,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonVolts'),
                    serial, 'powMonVolts', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonVoltMax'),
                    serial, 'powMonVoltMax', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('analogSensorAnalog'),
                    serial, 'powMonVoltMin', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonVoltPk'),
                    serial, 'powMonVoltPk', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonAmpsX10'),
                    serial, 'powMonAmpsX10', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonRealPow'),
                    serial, 'powMonRealPow', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonAppPow'),
                    serial, 'powMonAppPow', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonPwrFact'),
                    serial, 'powMonPwrFact', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonOutlet1'),
                    serial, 'powMonOutlet1', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonOutlet2'),
                    serial, 'powMonOutlet2', name=name))
        return sensors

    @for_table("powerOnlyTable")
    def _get_power_only_params(self, power_only_sensors):
        sensors = []
        for power_sensor in itervalues(power_only_sensors):
            power_sensor_avail = power_sensor.get('powerAvail', None)
            if power_sensor_avail:
                power_sensor_oid = power_sensor.get(0, None)
                serial = power_sensor.get('powerSerial', None)
                name = power_sensor.get('powerName', None)
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerVolts'), serial,
                    'powerVolts', u_o_m=Sensor.UNIT_VOLTS_DC, name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerAmps'), serial,
                    'powerAmps', u_o_m=Sensor.UNIT_AMPERES, name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerRealPow'),
                    serial, 'powerRealPow', name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerAppPow'),
                    serial, 'powerAppPow', name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerPwrFactor'),
                    serial, 'powerPwrFactor', name=name))
        return sensors

    @for_table("power3ChTable")
    def _get_power3_ch_params(self, power3_ch_sensors):
        sensors = []
        for pow3_ch_sensor in itervalues(power3_ch_sensors):
            pow3_ch_avail = pow3_ch_sensor.get('pow3ChAvail', None)
            if pow3_ch_avail:
                pow3_ch_sensor_oid = pow3_ch_sensor.get(0, None)
                serial = pow3_ch_sensor.get('pow3ChSerial', None)
                name = pow3_ch_sensor.get('pow3ChName', None)
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChKWattHrsA'),
                    serial, 'pow3ChKWattHrsA', u_o_m=Sensor.UNIT_WATTS,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltsA'),
                    serial, 'pow3ChVoltsA', u_o_m=Sensor.UNIT_WATTS,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltMaxA'),
                    serial, 'pow3ChVoltMaxA', u_o_m=Sensor.UNIT_WATTS,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltMinA'),
                    serial, 'pow3ChVoltMinA', Sensor.UNIT_WATTS, name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltPkA'),
                    serial, 'pow3ChVoltPkA', u_o_m=Sensor.UNIT_WATTS,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChAmpsX10A'),
                    serial, 'pow3ChAmpsX10A', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChRealPowA'),
                    serial, 'pow3ChRealPowA', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChAppPowA'),
                    serial, 'pow3ChAppPowA', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChPwrFactA'),
                    serial, 'pow3ChPwrFactA', name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChKWattHrsB'),
                    serial, 'pow3ChKWattHrsB', u_o_m=Sensor.UNIT_WATTS,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltsB'),
                    serial, 'pow3ChVoltsB', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltMaxB'),
                    serial, 'pow3ChVoltMaxB', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltMinB'),
                    serial, 'pow3ChVoltMinB', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltPkB'),
                    serial, 'pow3ChVoltPkB', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChAmpsX10B'),
                    serial, 'pow3ChAmpsX10B', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChRealPowB'),
                    serial, 'pow3ChRealPowB', name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChAppPowB'),
                    serial, 'pow3ChAppPowB', name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChPwrFactB'),
                    serial, 'pow3ChPwrFactB', name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChKWattHrsC'),
                    serial, 'pow3ChKWattHrsC', u_o_m=Sensor.UNIT_WATTS,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltsC'),
                    serial, 'pow3ChVoltsC', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltMaxC'),
                    serial, 'pow3ChVoltMaxC', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltMinC'),
                    serial, 'pow3ChVoltMinC', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChVoltPkC'),
                    serial, 'pow3ChVoltPkC', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChAmpsX10C'),
                    serial, 'pow3ChAmpsX10C', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChRealPowC'),
                    serial, 'pow3ChRealPowC', name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChAppPowC'),
                    serial, 'pow3ChAppPowC', name=name))
                sensors.append(self._make_result_dict(
                    pow3_ch_sensor_oid,
                    self._get_oid_for_sensor('pow3ChPwrFactC'),
                    serial, 'pow3ChPwrFactC', name=name))
        return sensors

    @for_table("outletTable")
    def _get_outlet_params(self, outlet_sensors):
        sensors = []
        for outlet_sensor in itervalues(outlet_sensors):
            outlet_avail = outlet_sensor.get('outletAvail', None)
            if outlet_avail:
                outlet_oid = outlet_sensor.get(0, None)
                serial = outlet_sensor.get('outletSerial', None)
                name = outlet_sensor.get('outletName', None)
                sensors.append(self._make_result_dict(
                    outlet_oid,
                    self._get_oid_for_sensor('outlet1Status'),
                    serial, 'outlet1Status', name=name))
                sensors.append(self._make_result_dict(
                    outlet_oid,
                    self._get_oid_for_sensor('outlet2Status'),
                    serial, 'outlet2Status', name=name))
        return sensors

    @for_table("vsfcTable")
    def _get_vsfc_params(self, vsfc_sensors):
        sensors = []
        for vsfc_sensor in itervalues(vsfc_sensors):
            vsfc_avail = vsfc_sensor.get('vsfcAvail', None)
            if vsfc_avail:
                vsfc_oid = vsfc_sensor.get(0, None)
                serial = vsfc_sensor.get('vsfcSerial', None)
                name = vsfc_sensor.get('vsfcName', None)
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcSetPointC'),
                    serial, 'vsfcSetPointC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcIntTempC'),
                    serial, 'vsfcIntTempC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcExt1TempC'),
                    serial, 'vsfcExt1TempC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcExt2TempC'),
                    serial, 'vsfcExt2TempC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcExt3TempC'),
                    serial, 'vsfcExt3TempC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcExt4TempC'),
                    serial, 'vsfcExt4TempC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcFanSpeed'),
                    serial, 'vsfcFanSpeed', u_o_m=Sensor.UNIT_RPM,
                    name=name))
        return sensors

    @for_table("ctrl3ChTable")
    def _get_ctrl3_ch_params(self, ctrl3_ch_sensors):
        sensors = []
        for ctrl3_ch_sensor in itervalues(ctrl3_ch_sensors):
            ctrl3_ch_avail = ctrl3_ch_sensor.get('ctrl3ChAvail', None)
            if ctrl3_ch_avail:
                ctrl3_ch_oid = ctrl3_ch_sensor.get(0, None)
                serial = ctrl3_ch_sensor.get('ctrl3ChSerial', None)
                name = ctrl3_ch_sensor.get('ctrl3ChName', None)
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChVoltsA'),
                    serial, 'ctrl3ChVoltsA', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChVoltPkA'),
                    serial, 'ctrl3ChVoltPkA', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAmpsA'),
                    serial, 'ctrl3ChAmpsA', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAmpPkA'),
                    serial, 'ctrl3ChAmpPkA', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChRealPowA'),
                    serial, 'ctrl3ChRealPowA', name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAppPowA'),
                    serial, 'ctrl3ChAppPowA', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChPwrFactA'),
                    serial, 'ctrl3ChPwrFactA', name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChVoltsB'),
                    serial, 'ctrl3ChVoltsB', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChVoltPkB'),
                    serial, 'ctrl3ChVoltPkB', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAmpsB'),
                    serial, 'ctrl3ChAmpsB', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAmpPkB'),
                    serial, 'ctrl3ChAmpPkB', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChRealPowB'),
                    serial, 'ctrl3ChRealPowB', name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAppPowB'),
                    serial, 'ctrl3ChAppPowB', name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChPwrFactB'),
                    serial, 'ctrl3ChPwrFactB', name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChVoltsC'),
                    serial, 'ctrl3ChVoltsC', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChVoltPkC'),
                    serial, 'ctrl3ChVoltPkC', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAmpsC'),
                    serial, 'ctrl3ChAmpsC', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAmpPkC'),
                    serial, 'ctrl3ChAmpPkC', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChRealPowC'),
                    serial, 'ctrl3ChRealPowC', name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChAppPowC'),
                    serial, 'ctrl3ChAppPowC', name=name))
                sensors.append(self._make_result_dict(
                    ctrl3_ch_oid,
                    self._get_oid_for_sensor('ctrl3ChPwrFactC'),
                    serial, 'ctrl3ChPwrFactC', name=name))
        return sensors

    @for_table("ctrlGrpAmpsTable")
    def _get_ctrl_grp_amps_params(self, ctrl_grp_amps_sensors):
        sensors = []
        for c_grp_amps_sensor in itervalues(ctrl_grp_amps_sensors):
            c_grp_amp_avail = c_grp_amps_sensor.get('ctrlGrpAmpsAvail', None)
            if c_grp_amp_avail:
                c_grp_amp_oid = c_grp_amps_sensor.get(0, None)
                serial = c_grp_amps_sensor.get('ctrlGrpAmpsSerial', None)
                name = c_grp_amps_sensor.get('ctrlGrpAmpsName', None)
                sensors.append(self._make_result_dict(
                    c_grp_amp_oid,
                    self._get_oid_for_sensor('ctrlGrpAmpsA'),
                    serial, 'ctrlGrpAmpsA', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    c_grp_amp_oid,
                    self._get_oid_for_sensor('ctrlGrpAmpsB'),
                    serial, 'ctrlGrpAmpsB', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    c_grp_amp_oid,
                    self._get_oid_for_sensor('ctrlGrpAmpsC'),
                    serial, 'ctrlGrpAmpsC', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    c_grp_amp_oid,
                    self._get_oid_for_sensor('ctrlGrpAmpsD'),
                    serial, 'ctrlGrpAmpsD', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    c_grp_amp_oid,
                    self._get_oid_for_sensor('ctrlGrpAmpsE'),
                    serial, 'ctrlGrpAmpsE', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    c_grp_amp_oid,
                    self._get_oid_for_sensor('ctrlGrpAmpsF'),
                    serial, 'ctrlGrpAmpsF', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
        return sensors

    @for_table("ctrlOutletTable")
    def _get_ctrl_outlet_params(self, ctrl_outlet_sensors):
        sensors = []
        for c_outlet_sensor in itervalues(ctrl_outlet_sensors):
            c_outlet_oid = c_outlet_sensor.get(0, None)
            serial = c_outlet_sensor.get('ctrlOutletGroup', None)
            name = c_outlet_sensor.get('ctrlOutletName', None)
            sensors.append(self._make_result_dict(
                c_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletStatus'),
                serial, 'ctrlOutletStatus', name=name))
            sensors.append(self._make_result_dict(
                c_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletFeedback'),
                serial, 'ctrlOutletFeedback', name=name))
            sensors.append(self._make_result_dict(
                c_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletPending'),
                serial, 'ctrlOutletPending', name=name))
            sensors.append(self._make_result_dict(
                c_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletAmps'),
                serial, 'ctrlOutletAmps', u_o_m=Sensor.UNIT_AMPERES,
                name=name))
            sensors.append(self._make_result_dict(
                c_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletUpDelay'),
                serial, 'ctrlOutletUpDelay', name=name))
            sensors.append(self._make_result_dict(
                c_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletDwnDelay'),
                serial, 'ctrlOutletDwnDelay', name=name))
            sensors.append(self._make_result_dict(
                c_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletRbtDelay'),
                serial, 'ctrlOutletRbtDelay', name=name))
        return sensors

    @for_table("dstsTable")
    def _get_dsts_params(self, dsts_sensors):
        sensors = []
        for dsts_sensor in itervalues(dsts_sensors):
            dsts_avail = dsts_sensor.get('dstsAvail', None)
            if dsts_avail:
                dsts_oid = dsts_sensor.get(0, None)
                serial = dsts_sensor.get('dstsSerial', None)
                name = dsts_sensor.get('dstsName', None)
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsVoltsA'), serial,
                    'dstsVoltsA', u_o_m=Sensor.UNIT_VOLTS_DC, name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsAmpsA'), serial,
                    'dstsAmpsA', u_o_m=Sensor.UNIT_AMPERES, name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsVoltsB'), serial,
                    'dstsVoltsB', u_o_m=Sensor.UNIT_VOLTS_DC, name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsAmpsB'), serial,
                    'dstsAmpsB', u_o_m=Sensor.UNIT_AMPERES, name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsSourceAActive'),
                    serial, 'dstsSourceAActive', name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsSourceBActive'),
                    serial, 'dstsSourceBActive', name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsPowerStatusA'),
                    serial, 'dstsPowerStatusA', name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsPowerStatusB'),
                    serial, 'dstsPowerStatusB', name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsSourceATempC'),
                    serial, 'dstsSourceATempC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    dsts_oid,
                    self._get_oid_for_sensor('dstsSourceBTempC'),
                    serial, 'dstsSourceBTempC', u_o_m=Sensor.UNIT_CELCIUS,
                    name=name))
        return sensors

    @defer.inlineCallbacks
    def _get_sensor_count(self):
        """Count all available sensors in this WxGoose"""
        sensor_counts_oid = self.mib['nodes']['sensorCounts']['oid']
        sensor_counts = yield self.retrieve_column('sensorCounts')
        mapped_counts = ((sensor_counts_oid + OID(key[0:1]), count)
                         for key, count in sensor_counts.items())

        result = dict((self.oid_name_map[oid], count)
                      for oid, count in mapped_counts
                      if oid in self.oid_name_map)
        self._logger.debug('ItWatchDogsMib:: _get_sensor_count: result = %s',
                           result)
        defer.returnValue(result)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ Try to retrieve all available sensors in this WxGoose"""
        sensor_counts = yield self._get_sensor_count()
        self._logger.debug('ItWatchDogsMib:: get_all_sensors: ip = %s',
                           self.agent_proxy.ip)

        tables = ((self.translate_counter_to_table(counter), count)
                  for counter, count in sensor_counts.items())
        tables = (table for table, count in tables
                  if table and count)

        result = []
        for table in tables:
            self._logger.debug('ItWatchDogsMib:: get_all_sensors: table = %s',
                               table)
            sensors = yield self.retrieve_table(table).addCallback(
                                                                reduce_index)
            self._logger.debug('ItWatchDogsMib:: get_all_sensors: %s = %s',
                               table, sensors)
            handler = for_table.map.get(table, None)
            if not handler:
                self._logger.error("There is not data handler for %s", table)
            else:
                method = getattr(self, handler)
                result.extend(method(sensors))

        defer.returnValue(result)

    @classmethod
    def translate_counter_to_table(cls, counter_name):
        """Translates the name of a count object under sensorCounts into its
        corresponding sensor table object name.

        If unable to translate the counter name into a table name, None is
        returned.

        """
        counter_bases = [counter_name.replace('Count', '').lower(),
                         counter_name.replace('SensorCount', '').lower()]
        suffixes = ['table', 'sensortable', 'monitortable']
        alternatives = [base + suffix
                        for base in counter_bases for suffix in suffixes]

        for alt in alternatives:
            if alt in cls.lowercase_nodes:
                return cls.lowercase_nodes[alt]

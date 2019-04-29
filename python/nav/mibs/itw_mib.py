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
from nav.smidumps import get_mib
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
    mib = get_mib('IT-WATCHDOGS-MIB')

    oid_name_map = dict((OID(attrs['oid']), name)
                        for name, attrs in mib['nodes'].items())

    lowercase_nodes = dict((key.lower(), key)
                           for key in mib['nodes'])

    def _get_oid_for_sensor(self, sensor_name):
        """Return the OID for the given sensor-name as a string; Return
        None if sensor-name is not found.
        """
        oid_str = None
        nodes = self.mib.get('nodes')
        if nodes:
            sensor_def = nodes.get(sensor_name)
            if sensor_def:
                oid_str = sensor_def.get('oid')
        return oid_str

    def _make_result_dict(self, sensor_oid, base_oid, serial, desc,
                          u_o_m=None, precision=0, scale=None, name=None):
        """ Make a simple dictionary to return to plugin"""
        if not sensor_oid or not base_oid or not serial or not desc:
            return {}
        oid = OID(base_oid) + OID(sensor_oid)
        internal_name = serial + desc
        return {'oid': oid,
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
            available = climate_sensor.get('climateAvail')
            if available:
                climate_oid = climate_sensor.get(0)
                serial = climate_sensor.get('climateSerial')
                name = climate_sensor.get('climateName')

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateTempC'),
                    serial, 'climateTempC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateHumidity'),
                    serial, 'climateHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY, name=name))

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
            temp_sensor_avail = temp_sensor.get('tempSensorAvail')
            if temp_sensor_avail:
                temp_oid = temp_sensor.get(0)
                serial = temp_sensor.get('tempSensorSerial', 0)
                name = temp_sensor.get('tempSensorName')
                sensors.append(self._make_result_dict(
                    temp_oid,
                    self._get_oid_for_sensor('tempSensorTempC'),
                    serial, 'tempSensorTempC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
        return sensors

    @for_table('airFlowSensorTable')
    def _get_air_flow_sensors_params(self, air_flow_sensors):
        """ Collect all airflow sensors and corresponding parameters"""
        sensors = []
        for air_flow_sensor in itervalues(air_flow_sensors):
            air_flow_avail = air_flow_sensor.get('airFlowSensorAvail')
            if air_flow_avail:
                air_flow_oid = air_flow_sensor.get(0)
                serial = air_flow_sensor.get('airFlowSensorSerial')
                name = air_flow_sensor.get('airFlowSensorName')
                sensors.append(self._make_result_dict(
                    air_flow_oid,
                    self._get_oid_for_sensor('airFlowSensorFlow'),
                    serial, 'airFlowSensorFlow', name=name))

                sensors.append(self._make_result_dict(
                    air_flow_oid,
                    self._get_oid_for_sensor('airFlowSensorTempC'),
                    serial, 'airFlowSensorTempC',
                    u_o_m=Sensor.UNIT_CELSIUS, name=name))

                sensors.append(self._make_result_dict(
                    air_flow_oid,
                    self._get_oid_for_sensor('airFlowSensorHumidity'),
                    serial, 'airFlowSensorHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY, name=name))
        return sensors

    @for_table('doorSensorTable')
    def _get_door_sensors_params(self, door_sensors):
        """ Collect all door sensors and corresponding parameters"""
        sensors = []
        for door_sensor in itervalues(door_sensors):
            door_sensor_avail = door_sensor.get('doorSensorAvail')
            if door_sensor_avail:
                door_sensor_oid = door_sensor.get(0)
                serial = door_sensor.get('doorSensorSerial')
                name = door_sensor.get('doorSensorName')
                sensors.append(self._make_result_dict(
                    door_sensor_oid,
                    self._get_oid_for_sensor('doorSensorStatus'),
                    serial, 'doorSensorStatus', name=name))
        return sensors

    @for_table('waterSensorTable')
    def _get_water_sensors_params(self, water_sensors):
        """ Collect all water sensors and corresponding parameters"""
        sensors = []
        self._logger.debug('_get_water_sensors_params: %s' % water_sensors)
        for water_sensor in itervalues(water_sensors):
            water_sensor_avail = water_sensor.get('waterSensorAvail', 0)
            if water_sensor_avail:
                water_sensor_oid = water_sensor.get(0)
                serial = water_sensor.get('waterSensorSerial')
                name = water_sensor.get('waterSensorName')
                sensors.append(self._make_result_dict(
                    water_sensor_oid,
                    self._get_oid_for_sensor('waterSensorDampness'),
                    serial, 'waterSensorDampness', name=name))
        return sensors

    @for_table('currentMonitorTable')
    def _get_current_monitors_params(self, current_monitors):
        sensors = []
        for current_mon in itervalues(current_monitors):
            current_mon_avail = current_mon.get('currentMonitorAvail')
            if current_mon_avail:
                current_mon_oid = current_mon.get(0)
                serial = current_mon.get('currentMonitorSerial')
                name = current_mon.get('currentMonitorName')
                sensors.append(self._make_result_dict(
                    current_mon_oid,
                    self._get_oid_for_sensor('currentMonitorAmps'),
                    serial, 'currentMonitorAmps',
                    u_o_m=Sensor.UNIT_AMPERES, scale='milli',
                    name=name))
        return sensors

    @for_table('millivoltMonitorTable')
    def _get_millivolt_monitors_params(self, millivolt_monitors):
        sensors = []
        for millivolt_mon in itervalues(millivolt_monitors):
            millivolt_mon_avail = millivolt_mon.get('millivoltMonitorAvail')
            if millivolt_mon_avail:
                millivolt_mon_oid = millivolt_mon.get(0)
                serial = millivolt_mon.get('millivoltMonitorSerial')
                name = millivolt_mon.get('millivoltMonitorName')
                sensors.append(self._make_result_dict(
                    millivolt_mon_oid,
                    self._get_oid_for_sensor('millivoltMonitorMV'),
                    serial, 'millivoltMonitorMV', u_o_m=Sensor.UNIT_VOLTS_DC,
                    scale='milli', name=name))
        return sensors

    @for_table('dewPointSensorTable')
    def _get_dewpoint_sensors_params(self, dewpoint_sensors):
        sensors = []
        for dewpoint_sensor in itervalues(dewpoint_sensors):
            dewpoint_sensor_avail = dewpoint_sensor.get('dewPointSensorAvail')
            if dewpoint_sensor_avail:
                dewpoint_sensor_oid = dewpoint_sensor.get(0)
                serial = dewpoint_sensor.get('dewPointSensorSerial')
                name = dewpoint_sensor.get('dewPointSensorName')
                sensors.append(self._make_result_dict(
                    dewpoint_sensor_oid,
                    self._get_oid_for_sensor('dewPointSensorDewPoint'),
                    serial, 'dewPointSensorDewPoint',
                    u_o_m=Sensor.UNIT_CELSIUS, name=name))

                sensors.append(self._make_result_dict(
                    dewpoint_sensor_oid,
                    self._get_oid_for_sensor('dewPointSensorTempC'),
                    serial, 'dewPointSensorTempC',
                    u_o_m=Sensor.UNIT_CELSIUS, name=name))

                sensors.append(self._make_result_dict(
                    dewpoint_sensor_oid,
                    self._get_oid_for_sensor('dewPointSensorHumidity'),
                    serial, 'dewPointSensorHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY, name=name))
        return sensors

    @for_table('digitalSensorTable')
    def _get_digital_sensors_params(self, digital_sensors):
        sensors = []
        for digital_sensor in itervalues(digital_sensors):
            digital_avail = digital_sensor.get('digitalSensorAvail')
            if digital_avail:
                digital_sensor_oid = digital_sensor.get(0)
                serial = digital_sensor.get('digitalSensorSerial')
                name = digital_sensor.get('digitalSensorName')
                sensors.append(self._make_result_dict(
                    digital_sensor_oid,
                    self._get_oid_for_sensor('digitalSensorDigital'),
                    serial, 'digitalSensorDigital', name=name))
        return sensors

    @for_table('cpmSensorTable')
    def _get_cpm_sensors_params(self, cpm_sensors):
        sensors = []
        for cpm_sensor in itervalues(cpm_sensors):
            cpm_sensor_avail = cpm_sensor.get('cpmSensorAvail')
            if cpm_sensor_avail:
                cpm_sensor_oid = cpm_sensor.get(0)
                serial = cpm_sensor.get('cpmSensorSerial')
                name = cpm_sensor.get('cpmSensorName')
                sensors.append(self._make_result_dict(
                    cpm_sensor_oid,
                    self._get_oid_for_sensor('cpmSensorStatus'),
                    serial, 'cpmSensorStatus', name=name))
        return sensors

    @for_table('smokeAlarmTable')
    def _get_smoke_alarms_params(self, smoke_alarms):
        sensors = []
        for smoke_alarm in itervalues(smoke_alarms):
            smoke_alarm_avail = smoke_alarm.get('smokeAlarmAvail')
            if smoke_alarm_avail:
                smoke_alarm_oid = smoke_alarm.get(0)
                serial = smoke_alarm.get('smokeAlarmSerial')
                name = smoke_alarm.get('smokeAlarmName')
                sensors.append(self._make_result_dict(
                    smoke_alarm_oid,
                    self._get_oid_for_sensor('smokeAlarmStatus'),
                    serial, 'smokeAlarmStatus', name=name))
        return sensors

    @for_table('neg48VdcSensorTable')
    def _get_neg48vdc_sensors_params(self, neg48vdc_sensors):
        sensors = []
        for neg48vdc_sensor in itervalues(neg48vdc_sensors):
            neg48vdc_sensor_avail = neg48vdc_sensor.get('neg48VdcSensorAvail')
            if neg48vdc_sensor_avail:
                neg48vdc_sensor_oid = neg48vdc_sensor.get(0)
                serial = neg48vdc_sensor.get('neg48VdcSensorSerial')
                name = neg48vdc_sensor.get('neg48VdcSensorName')
                sensors.append(self._make_result_dict(
                    neg48vdc_sensor_oid,
                    self._get_oid_for_sensor('neg48VdcSensorVoltage'),
                    serial, 'neg48VdcSensorVoltage',
                    u_o_m=Sensor.UNIT_VOLTS_DC, name=name))
        return sensors

    @for_table('pos30VdcSensorTable')
    def _get_pos30vdc_sensors_params(self, pos30vdc_sensors):
        sensors = []
        for pos30vdc_sensor in itervalues(pos30vdc_sensors):
            pos30vdc_sensor_avail = pos30vdc_sensor.get('pos30VdcSensorAvail')
            if pos30vdc_sensor_avail:
                pos30vdc_sensor_oid = pos30vdc_sensor.get(0)
                serial = pos30vdc_sensor.get('pos30VdcSensorSerial')
                name = pos30vdc_sensor.get('pos30VdcSensorName')
                sensors.append(self._make_result_dict(
                    pos30vdc_sensor_oid,
                    self._get_oid_for_sensor('pos30VdcSensorVoltage'),
                    serial, 'pos30VdcSensorVoltage', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
        return sensors

    @for_table('analogSensorTable')
    def _get_analog_sensors_params(self, analog_sensors):
        sensors = []
        for analog_sensor in itervalues(analog_sensors):
            analog_avail = analog_sensor.get('analogSensorAvail')
            if analog_avail:
                analog_sensor_oid = analog_sensor.get(0)
                serial = analog_sensor.get('analogSensorSerial')
                name = analog_sensor.get('analogSensorName')
                sensors.append(self._make_result_dict(
                    analog_sensor_oid,
                    self._get_oid_for_sensor('analogSensorAnalog'),
                    serial, 'analogSensorAnalog', name=name))
        return sensors

    @for_table('powerMonitorTable')
    def _get_power_monitor_params(self, power_monitor_sensors):
        sensors = []
        for pow_mon_sensor in itervalues(power_monitor_sensors):
            pow_mon_avail = pow_mon_sensor.get('powMonAvail')
            if pow_mon_avail:
                pow_mon_oid = pow_mon_sensor.get(0)
                serial = pow_mon_sensor.get('powMonSerial')
                name = pow_mon_sensor.get('powMonName')
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

    @for_table('powerOnlyTable')
    def _get_power_only_params(self, power_sensors):
        sensors = []
        for power_sensor in itervalues(power_sensors):
            power_sensor_avail = power_sensor.get('powerAvail')
            if power_sensor_avail:
                power_sensor_oid = power_sensor.get(0)
                serial = power_sensor.get('powerSerial')
                name = power_sensor.get('powerName')
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerVolts'), serial,
                    'powerVolts', u_o_m=Sensor.UNIT_VOLTS_DC, name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerAmps'),
                    serial, 'powerAmps', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
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

    @for_table('power3ChTable')
    def _get_power3_ch_params(self, power3_ch_sensors):
        sensors = []
        for pow3_ch_sensor in itervalues(power3_ch_sensors):
            pow3_ch_avail = pow3_ch_sensor.get('pow3ChAvail')
            if pow3_ch_avail:
                power3_ch_sensor_oid = pow3_ch_sensor.get(0)
                serial = pow3_ch_sensor.get('pow3ChSerial')
                name = pow3_ch_sensor.get('pow3ChName')
                # sensors with postfix A - C
                for port in ('A', 'B', 'C'):
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChKWattHrs' + port),
                        serial, 'pow3ChKWattHrs' + port,
                        u_o_m=Sensor.UNIT_WATTHOURS,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChVolts' + port),
                        serial, 'pow3ChVolts' + port,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChVoltMax' + port),
                        serial, 'pow3ChVoltMax' + port,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChVoltMin' + port),
                        serial, 'pow3ChVoltMin' + port,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChVoltPk' + port),
                        serial, 'pow3ChVoltPk' + port,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChAmpsX10' + port),
                        serial, 'pow3ChAmpsX10' + port,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChRealPow' + port),
                        serial, 'pow3ChRealPow' + port,
                        u_o_m=Sensor.UNIT_WATTS,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChAppPow' + port),
                        serial, 'pow3ChAppPow' + port,
                        u_o_m=Sensor.UNIT_VOLTAMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        power3_ch_sensor_oid,
                        self._get_oid_for_sensor('pow3ChPwrFact' + port),
                        serial, 'pow3ChPwrFact' + port, name=name))
        return sensors

    @for_table('outletTable')
    def _get_outlet_params(self, outlet_sensors):
        sensors = []
        for outlet_sensor in itervalues(outlet_sensors):
            outlet_avail = outlet_sensor.get('outletAvail')
            if outlet_avail:
                outlet_oid = outlet_sensor.get(0)
                serial = outlet_sensor.get('outletSerial')
                name = outlet_sensor.get('outletName')
                sensors.append(self._make_result_dict(
                    outlet_oid,
                    self._get_oid_for_sensor('outlet1Status'),
                    serial, 'outlet1Status', name=name))
                sensors.append(self._make_result_dict(
                    outlet_oid,
                    self._get_oid_for_sensor('outlet2Status'),
                    serial, 'outlet2Status', name=name))
        return sensors

    @for_table('vsfcTable')
    def _get_vsfc_params(self, vsfc_sensors):
        sensors = []
        for vsfc_sensor in itervalues(vsfc_sensors):
            vsfc_avail = vsfc_sensor.get('vsfcAvail')
            if vsfc_avail:
                vsfc_oid = vsfc_sensor.get(0)
                serial = vsfc_sensor.get('vsfcSerial')
                name = vsfc_sensor.get('vsfcName')
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcSetPointC'),
                    serial, 'vsfcSetPointC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcFanSpeed'),
                    serial, 'vsfcFanSpeed', u_o_m=Sensor.UNIT_RPM,
                    name=name))
                sensors.append(self._make_result_dict(
                    vsfc_oid,
                    self._get_oid_for_sensor('vsfcIntTempC'),
                    serial, 'vsfcIntTempC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
                # sensors for ports 1 - 4
                for port in range(1, 5):
                    sensor_key = 'vsfcExt' + str(port) + 'TempC'
                    sensors.append(self._make_result_dict(
                        vsfc_oid,
                        self._get_oid_for_sensor(sensor_key), serial,
                        sensor_key, u_o_m=Sensor.UNIT_CELSIUS, name=name))
        return sensors

    @for_table('ctrl3ChTable')
    def _get_ctrl3_ch_params(self, ctrl3_ch_sensors):
        sensors = []
        for ctrl3_ch_sensor in itervalues(ctrl3_ch_sensors):
            ctrl3_ch_avail = ctrl3_ch_sensor.get('ctrl3ChAvail')
            if ctrl3_ch_avail:
                ctrl3_ch_oid = ctrl3_ch_sensor.get(0)
                serial = ctrl3_ch_sensor.get('ctrl3ChSerial')
                name = ctrl3_ch_sensor.get('ctrl3ChName')
                # sensors A - C
                for pfix in ('A', 'B', 'C'):
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChVolts' + pfix),
                        serial, 'ctrl3ChVolts' + pfix,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChVoltPk' + pfix),
                        serial, 'ctrl3ChVoltPk' + pfix,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChAmps' + pfix),
                        serial, 'ctrl3ChAmps' + pfix,
                        u_o_m=Sensor.UNIT_AMPERES, name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChAmpPk' + pfix),
                        serial, 'ctrl3ChAmpPk' + pfix,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChRealPow' + pfix),
                        serial, 'ctrl3ChRealPow' + pfix,
                        u_o_m=Sensor.UNIT_WATTS,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChAppPow' + pfix),
                        serial, 'ctrl3ChAppPow' + pfix,
                        u_o_m=Sensor.UNIT_VOLTAMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChPwrFact' + pfix),
                        serial, 'ctrl3ChPwrFact' + pfix, name=name))
        return sensors

    @for_table('ctrlGrpAmpsTable')
    def _get_ctrl_grp_amps_params(self, ctrl_grp_amps_sensors):
        sensors = []
        for ctrl_grp_amps_sensor in itervalues(ctrl_grp_amps_sensors):
            ctrl_grp_amp_avail = ctrl_grp_amps_sensor.get('ctrlGrpAmpsAvail')
            if ctrl_grp_amp_avail:
                ctrl_grp_amp_oid = ctrl_grp_amps_sensor.get(0)
                serial = ctrl_grp_amps_sensor.get('ctrlGrpAmpsSerial')
                name = ctrl_grp_amps_sensor.get('ctrlGrpAmpsName')
                for pfix in ('A', 'B', 'C', 'D', 'E', 'F'):
                    sensors.append(self._make_result_dict(
                        ctrl_grp_amp_oid,
                        self._get_oid_for_sensor('ctrlGrpAmps' + pfix),
                        serial, 'ctrlGrpAmps' + pfix, u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
        return sensors

    @for_table('ctrlOutletTable')
    def _get_ctrl_outlet_params(self, ctrl_outlet_sensors):
        sensors = []
        for ctrl_outlet_sensor in itervalues(ctrl_outlet_sensors):
            ctrl_outlet_oid = ctrl_outlet_sensor.get(0)
            serial = ctrl_outlet_sensor.get('ctrlOutletGroup')
            name = ctrl_outlet_sensor.get('ctrlOutletName')
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletStatus'),
                serial, 'ctrlOutletStatus', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletFeedback'),
                serial, 'ctrlOutletFeedback', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletPending'),
                serial, 'ctrlOutletPending', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletAmps'),
                serial, 'ctrlOutletAmps', u_o_m=Sensor.UNIT_AMPERES,
                name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletUpDelay'),
                serial, 'ctrlOutletUpDelay', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletDwnDelay'),
                serial, 'ctrlOutletDwnDelay', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletRbtDelay'),
                serial, 'ctrlOutletRbtDelay', name=name))
        return sensors

    @for_table('dstsTable')
    def _get_dsts_params(self, dsts_sensors):
        sensors = []
        for dsts_sensor in itervalues(dsts_sensors):
            dsts_sensor_avail = dsts_sensor.get('dstsAvail')
            if dsts_sensor_avail:
                dsts_sensor_oid = dsts_sensor.get(0)
                serial = dsts_sensor.get('dstsSerial')
                name = dsts_sensor.get('dstsName')
                for pfix in ('A', 'B'):
                    sensors.append(self._make_result_dict(
                        dsts_sensor_oid,
                        self._get_oid_for_sensor('dstsVolts' + pfix),
                        serial, 'dstsVolts' + pfix, u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        dsts_sensor_oid,
                        self._get_oid_for_sensor('dstsAmps' + pfix),
                        serial, 'dstsAmps' + pfix,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        dsts_sensor_oid,
                        self._get_oid_for_sensor('dstsSource' + pfix + 'Active'),
                        serial, 'dstsSource' + pfix + 'Active', name=name))
                    sensors.append(self._make_result_dict(
                        dsts_sensor_oid,
                        self._get_oid_for_sensor('dstsPowerStatus' + pfix),
                        serial, 'dstsPowerStatus' + pfix, name=name))
                    sensors.append(self._make_result_dict(
                        dsts_sensor_oid,
                        self._get_oid_for_sensor('dstsSource' + pfix + 'TempC'),
                        serial, 'dstsSource' + pfix + 'TempC',
                        u_o_m=Sensor.UNIT_CELSIUS,
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
            handler = for_table.map.get(table)
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

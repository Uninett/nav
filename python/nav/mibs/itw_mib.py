# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs import mibretriever
from nav.oids import OID


def for_table(table_name):
    if not hasattr(for_table, 'map'):
        for_table.map = {}

    def decorate(method):
        for_table.map[table_name] = method.func_name
        return method

    return decorate

class ItWatchDogsMib(mibretriever.MibRetriever):
    from nav.smidumps.itw_mib import MIB as mib

    oid_name_map = dict((OID(attrs['oid']), name)
                        for name, attrs in mib['nodes'].items())

    lowercase_nodes = dict((key.lower(), key)
                           for key in mib['nodes'])

    def get_module_name(self):
        """ Return this official MIB-name"""
        return self.mib.get('moduleName', None)

    def _make_result_dict(self, sensor_oid, sensor_mib, serial, desc,
                                u_o_m=None, precision=0, scale=None, name=None):
        """ Make a simple dictionary to return to plugin"""
        if not sensor_oid or not sensor_mib or not serial or not desc:
            return {}
        oid = str(sensor_mib.oid) + str(sensor_oid)
        internal_name = serial + desc
        return {'oid': oid,
                'unit_of_measurement': u_o_m,
                'precision': precision,
                'scale': scale,
                'description': desc,
                'name': name,
                'internal_name': internal_name,
                'mib': self.get_module_name()
                }
        
    @for_table('climateTable')
    def _get_climate_sensors_params(self, climate_sensors):
        """ Collect all climate sensors and corresponding parameters"""
        sensors = []
        for idx, climate_sensor in climate_sensors.items():
            available = climate_sensor.get('climateAvail', None)
            if available:
                climate_oid = climate_sensor.get(0, None)
                serial = climate_sensor.get('climateSerial', None)
                name = climate_sensor.get('climateName', None)

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateTempC', None),
                                serial, 'climateTempC', u_o_m='celsius',
                                name=name))

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateHumidity', None),
                                serial, 'climateHumidity', u_o_m='percentRH',
                                name=name))
                
                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateAirflow', None),
                                serial, 'climateAirflow', name=name))

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateLight', None),
                                serial, 'climateLight', name=name))

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateSound', None),
                                serial, 'climateSound', name=name))

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateIO1', None),
                                serial, 'climateIO1', name=name))

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateIO2', None),
                                serial, 'climateIO2', name=name))

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateIO3', None),
                                serial, 'climateIO3', name=name))
        return sensors

    @for_table('tempSensorTable')
    def _get_temp_sensors_params(self, temp_sensors):
        """ Collect all temperature sensors and corresponding parameters"""
        sensors = []
        for idx, temp_sensor in temp_sensors.items():
            temp_sensor_avail = temp_sensor.get('tempSensorAvail', None)
            if temp_sensor_avail:
                temp_oid = temp_sensor.get(0, None)
                serial = temp_sensor.get('tempSensorSerial', 0)
                name = temp_sensor.get('tempSensorName', None)
                sensors.append(self._make_result_dict(temp_oid,
                                self.nodes.get('tempSensorTempC', None),
                                serial, 'tempSensorTempC', u_o_m='celsius',
                                name=name))
        return sensors

    @for_table('airFlowSensorTable')
    def _get_airflow_sensors_params(self, airflow_sensors):
        """ Collect all airflow sensors and corresponding parameters"""
        sensors = []
        for idx, airflow_sensor in airflow_sensors.items():
            airflow_avail = airflow_sensor.get('airFlowSensorAvail', None)
            if airflow_avail:
                airflow_oid = airflow_sensor.get(0, None)
                serial = airflow_sensor.get('airFlowSensorSerial', None)
                name = airflow_sensor.get('airFlowSensorName', None)
                sensors.append(self._make_result_dict(airflow_oid,
                                self.nodes.get('airFlowSensorFlow', None),
                                serial, 'airFlowSensorFlow',
                                name=name))

                sensors.append(self._make_result_dict(airflow_oid,
                                self.nodes.get('airFlowSensorTempC', None),
                                serial, 'airFlowSensorTempC',
                                u_o_m='celsius',
                                name=name))

                sensors.append(self._make_result_dict(airflow_oid,
                                self.nodes.get('airFlowSensorHumidity', None),
                                serial, 'airFlowSensorHumidity',
                                u_o_m='percentRH',
                                name=name))
        return sensors

    @for_table('doorSensorTable')
    def _get_door_sensors_params(self, door_sensors):
        """ Collect all door sensors and corresponding parameters"""
        sensors = []
        for idx, door_sensor in door_sensors.items():
            door_avail = door_sensor.get('doorSensorAvail', None)
            if door_avail:
                door_oid = door_sensor.get(0, None)
                serial = door_sensor.get('doorSensorSerial', None)
                name = door_sensor.get('doorSensorName', None)
                sensors.append(self._make_result_dict(door_oid,
                                self.nodes.get('doorSensorStatus', None),
                                serial, 'doorSensorStatus',
                                name=name))
        return sensors

    @for_table('waterSensorTable')
    def _get_water_sensors_params(self, water_sensors):
        """ Collect all water sensors and corresponding parameters"""
        sensors = []
        self.logger.debug('_get_water_sensors_params: %s' % water_sensors)
        for idx, water_sensor in water_sensors.items():
            water_avail = water_sensor.get('waterSensorAvail', 0)
            if water_avail:
                water_oid = water_sensor.get(0, None)
                serial = water_sensor.get('waterSensorSerial', None)
                name = water_sensor.get('waterSensorName', None)
                sensors.append(self._make_result_dict(water_oid,
                                    self.nodes.get('waterSensorDampness', None),
                                    serial, 'waterSensorDampness', name=name))
        return sensors

    @for_table('currentMonitorTable')
    def _get_current_sensors_params(self, current_sensors):
        sensors = []
        for idx, current_sensor in current_sensors.items():
            current_avail = current_sensor.get('currentMonitorAvail', None)
            if current_avail:
                current_oid = current_sensor.get(0, None)
                serial = current_sensor.get('currentMonitorSerial', None)
                name = current_sensor.get('currentMonitorName', None)
                sensors.append(self._make_result_dict(amps_oid,
                                    self.nodes.get('currentMonitorAmps', None),
                                    serial, 'currentMonitorAmps',
                                    u_o_m='amperes', scale='milli', name=name))
        return sensors

    @for_table('millivoltMonitorTable')
    def _get_millivolt_sensors_params(self, millivolt_sensors):
        sensors = []
        for idx, millivolt_sensor in millivolt_sensors.items():
            millivolt_avail = millivolt_sensor.get('millivoltMonitorAvail',
                                                                        None)
            if millivolt_avail:
                millivolt_oid = millivolt_sensor.get(0, None)
                serial = millivolt_sensor.get('millivoltMonitorSerial', None)
                name = millivolt_sensor.get('millivoltMonitorName', None)
                sensors.append(self._make_result_dict(millivolt_oid,
                                    self.nodes.get('millivoltMonitorMV', None),
                                    serial, 'millivoltMonitorMV', u_o_m='volts',
                                    scale='milli', name=name))
        return sensors

    @for_table('dewPointSensorTable')
    def _get_dewpoint_sensors_params(self, dewpoint_sensors):
        sensors = []
        for idx, dewpoint_sensor in dewpoint_sensors.items():
            dewpoint_avail = dewpoint_sensor.get('dewPointSensorAvail', None)
            if dewpoint_avail:
                dewpoint_oid = dewpoint_sensor.get(0, None)
                serial = dewpoint_sensor.get('dewPointSensorSerial', None)
                name = dewpoint_sensor.get('dewPointSensorName', None)
                sensors.append(self._make_result_dict(dewpoint_oid,
                                self.nodes.get('dewPointSensorDewPoint', None),
                                serial, 'dewPointSensorDewPoint',
                                u_o_m='celsius', name=name))
                                    
                sensors.append(self._make_result_dict(dewpoint_oid,
                                self.nodes.get('dewPointSensorTempC', None),
                                serial, 'dewPointSensorTempC',
                                u_o_m='celsius', name=name))

                sensors.append(self._make_result_dict(dewpoint_oid,
                                self.nodes.get('dewPointSensorHumidity', None),
                                serial, 'dewPointSensorHumidity',
                                u_o_m='percentRH', name=name))
        return sensors

    @for_table('digitalSensorTable')
    def _get_digital_sensors_params(self, digital_sensors):
        sensors = []
        for idx, digital_sensor in digital_sensors.items():
            digital_avail = digital_sensor.get('digitalSensorAvail', None)
            if digital_avail:
                digital_oid = digital_sensor.get(0, None)
                serial = digital_sensor.get('digitalSensorSerial', None)
                name = digital_sensor.get('digitalSensorName', None)
                sensors.append(self._make_result_dict(digital_oid,
                                self.nodes.get('digitalSensorDigital', None),
                                serial, 'digitalSensorDigital', name=name))
        return sensors

    @for_table('cpmSensorTable')
    def _get_cpm_sensors_params(self, cpm_sensors):
        sensors = []
        for idx, cpm_sensor in cpm_sensors.items():
            cpm_avail = cpm_sensor.get('cpmSensorAvail', None)
            if cpm_avail:
                cpm_oid = cpm_sensor.get(0, None)
                serial = cpm_sensor.get('cpmSensorSerial', None)
                name = cpm_sensor.get('cpmSensorName', None)
                sensors.append(self._make_result_dic(cpm_oid,
                                self.nodes.get('cpmSensorStatus', None),
                                serial, 'cpmSensorStatus', name=name))
        return sensors

    @for_table('smokeAlarmTable')
    def _get_smoke_sensors_params(self, smoke_sensors):
        sensors = []
        for idx, smoke_sensor in smoke_sensors.items():
            smoke_avail = smoke_sensor.get('smokeAlarmAvail', None)
            if smoke_avail:
                smoke_oid = smoke_sensor.get(0, None)
                serial = smoke_sensor.get('smokeAlarmSerial', None)
                name = smoke_sensor.get('smokeAlarmName', None)
                sensors.append(self._make_result_dict(smoke_oid,
                                    self.nodes.get('smokeAlarmStatus', None),
                                    serial, 'smokeAlarmStatus',
                                    name=name))
        return sensors

    @for_table('neg48VdcSensorTable')
    def _get_neg48Vdc_sensors_params(self, neg48Vdc_sensors):
        sensors = []
        for idx, neg48Vdc_sensor in neg48Vdc_sensors.items():
            neg48Vdc_avail = neg48Vdc_sensor.get('neg48VdcSensorAvail', None)
            if neg48Vdc_avail:
                neg48Vdc_oid = neg48Vdc_sensor.get(0, None)
                serial = neg48Vdc_sensor.get('neg48VdcSensorSerial', None)
                name = neg48Vdc_sensor.get('neg48VdcSensorName', None)
                sensors.append(self._make_result_dict(neg48Vdc_oid,
                                self.nodes.get('neg48VdcSensorVoltage', None),
                                serial, 'neg48VdcSensorVoltage',
                                u_o_m='voltsDC', name=name))
        return sensors

    @for_table('pos30VdcSensorTable')
    def _get_pos30Vdc_sensors_params(self, pos30Vdc_sensors):
        sensors = []
        for idx, pos30Vdc_sensor in pos30Vdc_sensors.items():
            pos30Vdc_avail = pos30Vdc_sensor.get('pos30VdcSensorAvail', None)
            if pos30Vdc_avail:
                pos30Vdc_oid = pos30Vdc_sensor.get(0, None)
                serial = pos30Vdc_sensor.get('pos30VdcSensorSerial', None)
                name = pos30Vdc_sensor.get('pos30VdcSensorName', None)
                sensors.append(self._make_result_dict(pos30Vdc_oid,
                                self.nodes.get('pos30VdcSensorVoltage', None),
                                serial, 'pos30VdcSensorVoltage',
                                u_o_m='voltsDC', name=name))
        return sensors

    @for_table('analogSensorTable')
    def _get_analog_sensors_params(self, analog_sensors):
        sensors = []
        for idx, analog_sensor in analog_sensors.items():
            analog_avail = analog_sensor.get('analogSensorAvail', None)
            if analog_avail:
                analog_oid = analog_sensor.get(0, None)
                serial = analog_sensor.get('analogSensorSerial', None)
                name = analog_sensor.get('analogSensorName', None)
                sensors.append(self._make_result_dict(analog_oid,
                                self.nodes.get('analogSensorAnalog', None),
                                serial, 'analogSensorAnalog', name=name))
        return sensors


    @for_table("powerMonitorTable")
    def _get_power_monitor_params(self, power_monitors_sensors):
        sensors = []
        for idx, pow_mon_sensor in power_monitors_sensors.items():
            pow_mon_avail = pow_mon_sensor.get('powMonAvail', None)
            if pow_mon_avail:
                pow_mon_oid = pow_mon_sensor.get(0, None)
                serial = pow_mon_sensor.get('powMonSerial', None)
                name = pow_mon_sensor.get('powMonName', None)
                sensors.append(self._make_result_dict(pow_mon_oid, 
                                self.nodes.get('powMonKWattHrs', None), serial,
                                'powMonKWattHrs', u_o_m='watts', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonVolts', None), serial,
                                'powMonVolts', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonVoltMax', None), serial,
                                'powMonVoltMax', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonVoltMin', None),serial,
                                'powMonVoltMin', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonVoltPk', None), serial,
                                'powMonVoltPk', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonAmpsX10', None), serial,
                                'powMonAmpsX10', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonRealPow', None), serial,
                                'powMonRealPow', name=name))
                sensors.append(self._make_result_dic(pow_mon_oid,
                                self.nodes.get('powMonAppPow', None), serial,
                                'powMonAppPow', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonPwrFact', None), serial,
                                'powMonPwrFact', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonOutlet1', None), serial,
                                'powMonOutlet1', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonOutlet2', None), serial,
                                'powMonOutlet2', name=name))
        return sensors

    @for_table("powerOnlyTable")
    def _get_power_only_params(self, power_only_sensors):
        sensors = []
        for idx, power_sensor in power_only_sensors.items():
            power_sensor_avail = power_sensor.get('powerAvail', None)
            if power_sensor_avail:
                power_sensor_oid = power_sensor.get(0, None)
                serial = power_sensor.get('powerSerial', None)
                name = power_sensor.get('powerName', None)
                sensors.append(self._name_result_dict(power_sensor_oid,
                                self.nodes.get('powerVolts', None), serial,
                                'powerVolts', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerAmps', None), serial,
                                'powerAmps', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerRealPow', None), serial,
                                'powerRealPow', name=name))
                sensors.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerAppPow', None), serial,
                                'powerAppPow', name=name))
                sensors.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerPwrFactor', None), serial,
                                'powerPwrFactor', name=name))
        return sensors

    @for_table("power3ChTable")
    def _get_power3_ch_params(self, power3_ch_sensors):
        sensors = []
        for idx, pow3_ch_sensor in power3_ch_sensors.items():
            pow3_ch_avail = pow3_ch_sensor.get('pow3ChAvail', None)
            if pow3_ch_avail:
                pow3_ch_sensor_oid = pow3_ch_sensor.get(0, None)
                serial = pow3_ch_sensor.get('pow3ChSerial', None)
                name = pow3_ch_sensor.get('pow3ChName', None)
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChKWattHrsA', None), serial,
                                'pow3ChKWattHrsA', u_o_m='watts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltsA', None), serial,
                                'pow3ChVoltsA', u_o_m='watts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltMaxA', None), serial,
                                'pow3ChVoltMaxA', u_o_m='watts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltMinA', None), serial,
                                'pow3ChVoltMinA', 'watts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltPkA', None), serial,
                                'pow3ChVoltPkA', u_o_m='watts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChAmpsX10A', None), serial,
                                'pow3ChAmpsX10A', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChRealPowA', None), serial,
                                'pow3ChRealPowA', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChAppPowA', None), serial,
                                'pow3ChAppPowA', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChPwrFactA', None), serial,
                                'pow3ChPwrFactA', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChKWattHrsB', None), serial,
                                'pow3ChKWattHrsB', u_o_m='watts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltsB', None), serial,
                                'pow3ChVoltsB', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltMaxB', None), serial,
                                'pow3ChVoltMaxB', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltMinB', None), serial,
                                'pow3ChVoltMinB', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltPkB', None), serial,
                                'pow3ChVoltPkB', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChAmpsX10B', None), serial,
                                'pow3ChAmpsX10B', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChRealPowB', None), serial,
                                'pow3ChRealPowB', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChAppPowB', None), serial,
                                'pow3ChAppPowB', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChPwrFactB', None), serial,
                                'pow3ChPwrFactB', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChKWattHrsC', None), serial,
                                'pow3ChKWattHrsC', u_o_m='watts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltsC', None), serial,
                                'pow3ChVoltsC', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltMaxC', None), serial,
                                'pow3ChVoltMaxC', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltMinC', None), serial,
                                'pow3ChVoltMinC', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChVoltPkC', None), serial,
                                'pow3ChVoltPkC', u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChAmpsX10C', None), serial,
                                'pow3ChAmpsX10C', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChRealPowC', None), serial,
                                'pow3ChRealPowC', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChAppPowC', None), serial,
                                'pow3ChAppPowC', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('pow3ChPwrFactC', None), serial,
                                'pow3ChPwrFactC', name=name))
        return sensors

    @for_table("outletTable")
    def _get_outlet_params(self, outlet_sensors):
        sensors = []
        for idx, outlet_sensor in outlet_sensors.items():
            outlet_avail = outlet_sensor.get('outletAvail', None)
            if outlet_avail:
                outlet_oid = outlet_sensor.get(0, None)
                serial = outlet_sensor.get('outletSerial', None)
                name = outlet_sensor.get('outletName', None)
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('outlet1Status', None), serial,
                                'outlet1Status', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('outlet2Status', None), serial,
                                'outlet2Status', name=name))
        return sensors

    @for_table("vsfcTable")
    def _get_vsfc_params(self, vsfc_sensors):
        sensors = []
        for idx, vsfc_sensor in vsfc_sensors.items():
            vsfc_avail = vsfc_sensor.get('vsfcAvail', None)
            if vsfc_avail:
                vsfc_oid = vsfc_sensor.get(0, None)
                serial = vsfc_sensor.get('vsfcSerial', None)
                name = vsfc_sensor.get('vsfcName', None)
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('vsfcSetPointC', None), serial,
                                'vsfcSetPointC', u_o_m='celsius', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('vsfcIntTempC', None), serial,
                                'vsfcIntTempC', u_o_m='celsius', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('vsfcExt1TempC', None), serial,
                                'vsfcExt1TempC', u_o_m='celsius', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('vsfcExt2TempC', None), serial,
                                'vsfcExt2TempC', u_o_m='celsius', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('vsfcExt3TempC', None), serial,
                                'vsfcExt3TempC', u_o_m='celsius', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('vsfcExt4TempC', None), serial,
                                'vsfcExt4TempC', u_o_m='celsius', name=name))
                sensors.append(self._make_result_dict(pow3_ch_sensor_oid,
                                self.nodes.get('vsfcFanSpeed', None), serial,
                                'vsfcFanSpeed', u_o_m='rpm', name=name))
        return sensors

    @for_table("ctrl3ChTable")
    def _get_ctrl3_ch_params(self, ctrl3_ch_sensors):
        sensors = []
        for idx, ctrl3_ch_sensor in ctrl3_ch_sensors.items():
            ctrl3_ch_avail = ctrl3_ch_sensor.get('ctrl3ChAvail', None)
            if ctrl3_ch_avail:
                ctrl3_ch_oid = ctrl3_ch_sensor.get(0, None)
                serial = ctrl3_ch_sensor.get('ctrl3ChSerial', None)
                name= ctrl3_ch_sensor.get('ctrl3ChName', None)
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChVoltsA', None), serial,
                                'ctrl3ChVoltsA',u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChVoltPkA', None), serial,
                                'ctrl3ChVoltPkA',u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAmpsA', None), serial,
                                'ctrl3ChAmpsA',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAmpPkA', None), serial,
                                'ctrl3ChAmpPkA',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChRealPowA', None), serial,
                                'ctrl3ChRealPowA', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAppPowA', None), serial,
                                'ctrl3ChAppPowA',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChPwrFactA', None), serial,
                                'ctrl3ChPwrFactA', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChVoltsB', None), serial,
                                'ctrl3ChVoltsB',u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChVoltPkB', None), serial,
                                'ctrl3ChVoltPkB',u_o_m='volsta', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAmpsB', None), serial,
                                'ctrl3ChAmpsB',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAmpPkB', None), serial,
                                'ctrl3ChAmpPkB',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChRealPowB', None), serial,
                                'ctrl3ChRealPowB', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAppPowB', None), serial,
                                'ctrl3ChAppPowB', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChPwrFactB', None), serial,
                                'ctrl3ChPwrFactB',name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChVoltsC', None), serial,
                                'ctrl3ChVoltsC',u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChVoltPkC', None), serial,
                                'ctrl3ChVoltPkC',u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAmpsC', None), serial,
                                'ctrl3ChAmpsC',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAmpPkC', None), serial,
                                'ctrl3ChAmpPkC',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChRealPowC', None), serial,
                                'ctrl3ChRealPowC', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChAppPowC', None), serial,
                                'ctrl3ChAppPowC', name=name))
                sensors.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChPwrFactC', None), serial,
                                'ctrl3ChPwrFactC', name=name))
        return sensors

    @for_table("ctrlGrpAmpsTable")
    def _get_ctrl_grp_amps_params(self, ctrl_grp_amps_sensors):
        sensors = []
        for idx, c_grp_amps_sensor in ctrl_grp_amps_sensors.items():
            c_grp_amp_avail = c_grp_amps_sensor.get('ctrlGrpAmpsAvail', None)
            if c_grp_amp_avail:
                c_grp_amp_oid = c_grp_amps_sensor.get(0, None)
                serial = c_grp_amps_sensor.get('ctrlGrpAmpsSerial', None)
                name = c_grp_amps_sensor.get('ctrlGrpAmpsName', None)
                sensors.append(self._make_result_dict(c_grp_amp_oid,
                                self.nodes.get('ctrlGrpAmpsA', None), serial,
                                'ctrlGrpAmpsA', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(c_grp_amp_oid,
                                self.nodes.get('ctrlGrpAmpsB', None), serial,
                                'ctrlGrpAmpsB', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(c_grp_amp_oid,
                                self.nodes.get('ctrlGrpAmpsC', None), serial,
                                'ctrlGrpAmpsC', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(c_grp_amp_oid,
                                self.nodes.get('ctrlGrpAmpsD', None), serial,
                                'ctrlGrpAmpsD', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(c_grp_amp_oid,
                                self.nodes.get('ctrlGrpAmpsE', None), serial,
                                'ctrlGrpAmpsE', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(c_grp_amp_oid,
                                self.nodes.get('ctrlGrpAmpsF', None), serial,
                                'ctrlGrpAmpsF', u_o_m='amperes', name=name))
        return sensors

    @for_table("ctrlOutletTable")
    def _get_ctrl_outlet_params(self, ctrl_outlet_sensors):
        sensors = []
        for idx, c_outlet_sensor in ctrl_outlet_sensors.items():
            c_outlet_oid = c_outlet_sensor.get(0, None)
            serial = c_outlet_sensor.get('ctrlOutletGroup', None)
            name = c_outlet_sensor.get('ctrlOutletName', None)
            sensors.append(self._make_result_dict(c_outlet_oid,
                            self.nodes.get('ctrlOutletStatus', None), serial,
                            'ctrlOutletStatus', name=name))
            sensors.append(self._make_result_dict(c_outlet_oid,
                            self.nodes.get('ctrlOutletFeedback', None), serial,
                            'ctrlOutletFeedback', name=name))
            sensors.append(self._make_result_dict(c_outlet_oid,
                            self.nodes.get('ctrlOutletPending', None), serial,
                            'ctrlOutletPending', name=name))
            sensors.append(self._make_result_dict(c_outlet_oid,
                            self.nodes.get('ctrlOutletAmps', None), serial,
                            'ctrlOutletAmps', u_o_m='amperes', name=name))
            sensors.append(self._make_result_dict(c_outlet_oid,
                            self.nodes.get('ctrlOutletUpDelay', None), serial,
                            'ctrlOutletUpDelay', name=name))
            sensors.append(self._make_result_dict(c_outlet_oid,
                            self.nodes.get('ctrlOutletDwnDelay', None), serial,
                            'ctrlOutletDwnDelay', name=name))
            sensors.append(self._make_result_dict(c_outlet_oid,
                            self.nodes.get('ctrlOutletRbtDelay', None), serial,
                            'ctrlOutletRbtDelay', name=name))
        return sensors

    @for_table("dstsTable")
    def _get_dsts_params(self, dsts_sensors):
        sensors = []
        for idx, dsts_sensor in dsts_sensors.items():
            dsts_avail = dsts_sensor.get('dstsAvail', None)
            if dsts_avail:
                dsts_oid = dsts_sensor.get(0, None)
                serial = dsts_sensor.get('dstsSerial', None)
                name = dsts_sensor.get('dstsName', None)
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsVoltsA', None), serial,
                                'dstsVoltsA',u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsAmpsA', None), serial,
                                'dstsAmpsA',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsVoltsB', None), serial,
                                'dstsVoltsB',u_o_m='volts', name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsAmpsB', None), serial,
                                'dstsAmpsB',u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsSourceAActive', None),
                                serial, 'dstsSourceAActive',name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsSourceBActive', None),
                                serial, 'dstsSourceBActive',name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsPowerStatusA', None),
                                serial, 'dstsPowerStatusA', name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsPowerStatusB', None),
                                serial, 'dstsPowerStatusB', name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsSourceATempC', None),
                                serial, 'dstsSourceATempC',u_o_m='celsius',
                                name=name))
                sensors.append(self._make_result_dict(dsts_oid,
                                self.nodes.get('dstsSourceBTempC', None),
                                serial, 'dstsSourceBTempC',u_o_m='celsius',
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
        self.logger.debug('ItWatchDogsMib:: _get_sensor_count: result = %s',
                            result)
        defer.returnValue(result)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ Try to retrieve all available sensors in this WxGoose"""
        sensor_counts = yield self._get_sensor_count()
        self.logger.debug('ItWatchDogsMib:: get_all_sensors: ip = %s',
                          self.agent_proxy.ip)

        tables = ((self.translate_counter_to_table(counter), count)
                  for counter, count in sensor_counts.items())
        tables = (table for table, count in tables
                  if table and count)

        result = []
        for table in tables:
            self.logger.debug('ItWatchDogsMib:: get_all_sensors: table = %s',
                                    table)
            sensors = yield self.retrieve_table(table).addCallback(reduce_index)
            self.logger.debug('ItWatchDogsMib:: get_all_sensors: %s = %s',
                              table, sensors)
            handler = for_table.map.get(table, None)
            if not handler:
                self.logger.error("There is not data handler for %s", table)
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

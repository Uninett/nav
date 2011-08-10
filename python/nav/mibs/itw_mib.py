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

class ItWatchDogsMib(mibretriever.MibRetriever):
    from nav.smidumps.itw_mib import MIB as mib

    oid_name_map = dict((OID(attrs['oid']), name)
                        for name, attrs in mib['nodes'].items())

    climate_count = 0
    power_monitor_count = 0
    temp_sensor_count = 0
    airflow_sensor_count = 0
    power_only_count = 0
    door_sensor_count = 0
    water_sensor_count = 0
    current_sensor_count = 0
    millivolt_sensor_count = 0
    power3_ch_sensor_count = 0
    outlet_count = 0
    vsfc_count = 0
    ctrl3_ch_count = 0
    ctrl_grp_amps_count = 0
    ctrl_output_count = 0
    dewpoint_sensor_count = 0
    digital_sensor_count = 0
    dsts_sensor_count = 0
    cpm_sensor_count = 0
    smoke_alarm_sensor_count = 0
    neg48Vdc_sensor_count = 0
    pos30Vdc_sensor_count = 0
    analog_sensor_count = 0

    def get_module_name(self):
        """ Return this official MIB-name"""
        return self.mib.get('moduleName', None)

    def retrieve_std_columns(self):
        return self.retrieve_columns([
                    #'climateSerial',
                    #'climateName',
                    #'climateAvail',
                    #'climateTempC',
                    #'climateHumidity',
                    #'climateAirflow',
                    #'climateLight',
                    #'climateSound',
                    #'climateIO1',
                    #'climateIO2',
                    #'climateIO3',
                    #
                    'powMonSerial',
                    'powMonName',
                    'powMonAvail',
                    'powMonKWattHrs',
                    'powMonVolts',
                    'powMonVoltMax',
                    'powMonVoltMin',
                    'powMonVoltPk',
                    'powMonAmpsX10',
                    'powMonRealPow',
                    'powMonAppPow',
                    'powMonPwrFact',
                    'powMonOutlet1',
                    'powMonOutlet2',
                    #
                    #'tempSensorSerial',
                    #'tempSensorName',
                    #'tempSensorAvail',
                    #'tempSensorTempC',
                    #
                    #'airFlowSensorSerial',
                    #'airFlowSensorName',
                    #'airFlowSensorAvail',
                    #'airFlowSensorFlow',
                    #'airFlowSensorTempC',
                    #'airFlowSensorHumidity',
                    #
                    'powerSerial',
                    'powerName',
                    'powerAvail',
                    'powerVolts',
                    'powerAmps',
                    'powerRealPow',
                    'powerAppPow',
                    'powerPwrFactor',
                    #
                    #'doorSensorSerial',
                    #'doorSensorName',
                    #'doorSensorAvail',
                    #'doorSensorStatus',
                    #
                    #'waterSensorSerial',
                    #'waterSensorName',
                    #'waterSensorAvail',
                    #'waterSensorDampness',
                    #
                    #'currentMonitorSerial',
                    #'currentMonitorName',
                    #'currentMonitorAvail',
                    #'currentMonitorAmps',
                    #
                    #'millivoltMonitorSerial',
                    #'millivoltMonitorName',
                    #'millivoltMonitorAvail',
                    #'millivoltMonitorMV',
                    #
                    'pow3ChSerial',
                    'pow3ChName',
                    'pow3ChAvail',
                    'pow3ChKWattHrsA',
                    'pow3ChVoltsA',
                    'pow3ChVoltMaxA',
                    'pow3ChVoltMinA',
                    'pow3ChVoltPkA',
                    'pow3ChAmpsX10A',
                    'pow3ChRealPowA',
                    'pow3ChAppPowA',
                    'pow3ChPwrFactA',
                    'pow3ChKWattHrsB',
                    'pow3ChVoltsB',
                    'pow3ChVoltMaxB',
                    'pow3ChVoltMinB',
                    'pow3ChVoltPkB',
                    'pow3ChAmpsX10B',
                    'pow3ChRealPowB',
                    'pow3ChAppPowB',
                    'pow3ChPwrFactB',
                    'pow3ChKWattHrsC',
                    'pow3ChVoltsC',
                    'pow3ChVoltMaxC',
                    'pow3ChVoltMinC',
                    'pow3ChVoltPkC',
                    'pow3ChAmpsX10C',
                    'pow3ChRealPowC',
                    'pow3ChAppPowC',
                    'pow3ChPwrFactC',
                    #
                    'outletSerial',
                    'outletName',
                    'outletAvail',
                    'outlet1Status',
                    'outlet2Status',
                    #
                    'vsfcSerial',
                    'vsfcName',
                    'vsfcAvail',
                    'vsfcSetPointC',
                    'vsfcIntTempC',
                    'vsfcExt1TempC',
                    'vsfcExt2TempC',
                    'vsfcExt3TempC',
                    'vsfcExt4TempC',
                    'vsfcFanSpeed',
                    #
                    'ctrl3ChSerial',
                    'ctrl3ChName',
                    'ctrl3ChAvail',
                    'ctrl3ChVoltsA',
                    'ctrl3ChVoltPkA',
                    'ctrl3ChAmpsA',
                    'ctrl3ChAmpPkA',
                    'ctrl3ChRealPowA',
                    'ctrl3ChAppPowA',
                    'ctrl3ChPwrFactA',
                    'ctrl3ChVoltsB',
                    'ctrl3ChVoltPkB',
                    'ctrl3ChAmpsB',
                    'ctrl3ChAmpPkB',
                    'ctrl3ChRealPowB',
                    'ctrl3ChAppPowB',
                    'ctrl3ChPwrFactB',
                    'ctrl3ChVoltsC',
                    'ctrl3ChVoltPkC',
                    'ctrl3ChAmpsC',
                    'ctrl3ChAmpPkC',
                    'ctrl3ChRealPowC',
                    'ctrl3ChAppPowC',
                    'ctrl3ChPwrFactC',
                    #
                    'ctrlGrpAmpsSerial',
                    'ctrlGrpAmpsName',
                    'ctrlGrpAmpsAvail',
                    'ctrlGrpAmpsA',
                    'ctrlGrpAmpsB',
                    'ctrlGrpAmpsC',
                    'ctrlGrpAmpsD',
                    'ctrlGrpAmpsE',
                    'ctrlGrpAmpsF',
                    #
                    'ctrlOutletName',
                    'ctrlOutletStatus',
                    'ctrlOutletFeedback',
                    'ctrlOutletPending',
                    'ctrlOutletAmps',
                    'ctrlOutletGroup',
                    'ctrlOutletUpDelay',
                    'ctrlOutletDwnDelay',
                    'ctrlOutletRbtDelay',
                    'ctrlOutletURL',
                    #
                    #'dewPointSensorSerial',
                    #'dewPointSensorName',
                    #'dewPointSensorAvail',
                    #'dewPointSensorDewPoint',
                    #'dewPointSensorTempC',
                    #'dewPointSensorHumidity',
                    #
                    #'digitalSensorSerial',
                    #'digitalSensorName',
                    #'digitalSensorAvail',
                    #'digitalSensorDigital',
                    #
                    'dstsSerial',
                    'dstsName',
                    'dstsAvail',
                    'dstsVoltsA',
                    'dstsAmpsA',
                    'dstsVoltsB',
                    'dstsAmpsB',
                    'dstsSourceAActive',
                    'dstsSourceBActive',
                    'dstsPowerStatusA',
                    'dstsPowerStatusB',
                    'dstsSourceATempC',
                    'dstsSourceBTempC',
                    #
                    #'cpmSensorSerial',
                    #'cpmSensorName',
                    #'cpmSensorAvail',
                    #'cpmSensorStatus',
                    #
                    #'smokeAlarmSerial',
                    #'smokeAlarmName',
                    #'smokeAlarmAvail',
                    #'smokeAlarmStatus',
                    #
                    #'neg48VdcSensorSerial',
                    #'neg48VdcSensorName',
                    #'neg48VdcSensorAvail',
                    #'neg48VdcSensorVoltage',
                    #
                    #'pos30VdcSensorSerial',
                    #'pos30VdcSensorName',
                    #'pos30VdcSensorAvail',
                    #'pos30VdcSensorVoltage',
                    #
                    #'analogSensorSerial',
                    #'analogSensorName',
                    #'analogSensorAvail',
                    #'analogSensorAnalog',
                    ])

    def _retrieve_sensor_columns(self, columns):
        """Retrieve the given columns and reduce indexes"""
        df = self.retrieve_columns(columns)
        df.addCallback(reduce_index)
        return df

    def _get_climate_sensors(self):
        """ Get all the columns for climate sensor."""
        return self._retrieve_sensor_columns([
                            'climateSerial',
                            'climateName',
                            'climateAvail',
                            'climateTempC',
                            'climateHumidity',
                            'climateAirflow',
                            'climateLight',
                            'climateSound',
                            'climateIO1',
                            'climateIO2',
                            'climateIO3',
                            ])

    def _get_temp_sensors(self):
        """ Get all the columns for temperature sensor."""
        return self._retrieve_sensor_columns([
                            'tempSensorSerial',
                            'tempSensorName',
                            'tempSensorAvail',
                            'tempSensorTempC',
                            ])

    def _get_airflow_sensors(self):
        """ Get all the columns for airflow sensor."""
        return self._retrieve_sensor_columns([
                            'airFlowSensorSerial',
                            'airFlowSensorName',
                            'airFlowSensorAvail',
                            'airFlowSensorFlow',
                            'airFlowSensorTempC',
                            'airFlowSensorHumidity',
                            ])

    def _get_door_sensors(self):
        """ Get all the columns for door sensor."""
        return self._retrieve_sensor_columns([
                            'doorSensorSerial',
                            'doorSensorName',
                            'doorSensorAvail',
                            'doorSensorStatus',
                            ])

    def _get_water_sensors(self):
        """ Get all the columns for water sensor."""
        return self._retrieve_sensor_columns([
                            'waterSensorSerial',
                            'waterSensorName',
                            'waterSensorAvail',
                            'waterSensorDampness',
                            ])

    def _get_current_sensors(self):
        return self._retrieve_sensor_columns([
                            'currentMonitorSerial',
                            'currentMonitorName',
                            'currentMonitorAvail',
                            'currentMonitorAmps',
                            ])

    def _get_millivolt_sensors(self):
        return self._retrieve_sensor_columns([
                            'millivoltMonitorSerial',
                            'millivoltMonitorName',
                            'millivoltMonitorAvail',
                            'millivoltMonitorMV',
                            ])

    def _get_dewpoint_sensors(self):
        return self._retrieve_sensor_columns([
                            'dewPointSensorSerial',
                            'dewPointSensorName',
                            'dewPointSensorAvail',
                            'dewPointSensorDewPoint',
                            'dewPointSensorTempC',
                            'dewPointSensorHumidity',
                            ])

    def _get_digital_sensors(self):
        return self._retrieve_sensor_columns([
                            'digitalSensorSerial',
                            'digitalSensorName',
                            'digitalSensorAvail',
                            'digitalSensorDigital',
                            ])

    def _get_cpm_sensors(self):
        return self._retrieve_sensor_columns([
                            'cpmSensorSerial',
                            'cpmSensorName',
                            'cpmSensorAvail',
                            'cpmSensorStatus',
                            ])

    def _get_smoke_sensors(self):
        return self._retrieve_sensor_columns([
                            'smokeAlarmSerial',
                            'smokeAlarmName',
                            'smokeAlarmAvail',
                            'smokeAlarmStatus',
                            ])

    def _get_neg48Vdc_sensors(self):
        return self._retrieve_sensor_columns([
                            'neg48VdcSensorSerial',
                            'neg48VdcSensorName',
                            'neg48VdcSensorAvail',
                            'neg48VdcSensorVoltage',
                            ])

    def _get_pos30Vdc_sensors(self):
        return self._retrieve_sensor_columns([
                            'pos30VdcSensorSerial',
                            'pos30VdcSensorName',
                            'pos30VdcSensorAvail',
                            'pos30VdcSensorVoltage',
                            ])

    def _get_analog_sensors(self):
        return self._retrieve_sensor_columns([
                            'analogSensorSerial',
                            'analogSensorName',
                            'analogSensorAvail',
                            'analogSensorAnalog',
                            ])

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

    def _get_water_sensors_params(self, water_sensors):
        """ Collect all water sensors and corresponding parameters"""
        sensors = []
        self.logger.error('_get_water_sensors_params: %s' % water_sensors)
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

    def _get_smoke_sensors_params(self, smoke_sensors):
        sensors = []
        for idx, smoke_sensor in smoke_sensors.items():
            smoke_avail = smoke_sensor.get('smokeAlarmAvail', None)
            if smoke_aval:
                smoke_oid = smoke_sensor.get(0, None)
                serial = smoke_sensor.get('smokeAlarmSerial', None)
                name = smoke_sensor.get('smokeAlarmName', None)
                sensors.append(self._make_result_dict(smoke_oid,
                                    self.nodes.get('smokeAlarmStatus', None),
                                    serial, 'smokeAlarmStatus',
                                    name=name))
        return sensors

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
        defer.returnValue(result)

    def _set_sensor_count(self, sensor_count):
        """ Store the count of sensors for late use"""
        self.logger.error('_set_sensor_count: %s' % sensor_count)

        self.climate_count = sensor_count.get('climateCount', 0)
        self.power_monitor_count = sensor_count.get('powerMonitorCount', 0)
        self.temp_sensor_count = sensor_count.get('tempSensorCount', 0)
        self.airflow_sensor_count = sensor_count.get(
                                    'airflowSensorCount', 0)
        self.power_only_count = sensor_count.get('powerOnlyCount', 0)
        self.door_sensor_count = sensor_count.get('doorSensorCount', 0)
        self.water_sensor_count = sensor_count.get('waterSensorCount', 0)
        self.current_sensor_count = sensor_count.get(
                                                'currentSensorCount', 0)
        self.millivolt_sensor_count = sensor_count.get(
                                            'millivoltSensorCount', 0)
        self.power3_ch_sensor_count = sensor_count.get(
                                            'power3ChSensorCount', 0)
        self.outlet_count = sensor_count.get('outletCount', 0)
        self.vsfc_count = sensor_count.get('vsfcCount', 0)
        self.ctrl3_ch_count = sensor_count.get('ctrl3ChCount', 0)
        self.ctrl_grp_amps_count = sensor_count.get('ctrlGrpAmpsCount', 0)
        self.ctrl_output_count = sensor_count.get('ctrlOutputCount', 0)
        self.dewpoint_sensor_count = sensor_count.get(
                                                'dewpointSensorCount', 0)
        self.digital_sensor_count = sensor_count.get(
                                                'digitalSensorCount', 0)
        self.dsts_sensor_count = sensor_count.get('dstsSensorCount', 0)
        self.cpm_sensor_count = sensor_count.get('cpmSensorCount', 0)
        self.smoke_alarm_sensor_count = sensor_count.get(
                                                'smokeAlarmSensorCount', 0)
        self.neg48Vdc_sensor_count = sensor_count.get(
                                                'neg48VdcSensorCount', 0)
        self.pos30Vdc_sensor_count = sensor_count.get(
                                                'pos30VdcSensorCount', 0)
        self.analog_sensor_count = sensor_count.get('analogSensorCount', 0)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ Try to retrieve all available sensors in this WxGoose"""
        sensor_counts = yield self._get_sensor_count()
        self._set_sensor_count(sensor_counts)
        self.logger.error('ItWatchDogsMib:: get_all_sensors: ip = %s' %
                            self.agent_proxy.ip)

        result = []
        if self.climate_count:
            climate_sensors = yield self._get_climate_sensors()
            self.logger.error(
                'ItWatchDogsMib:: get_all_sensors: climate_sensors = %s' %
                    climate_sensors)
            for row_id, row in climate_sensors.items():
                self.logger.debug(
                            'ItWatchDogsMib:: get_all_sensors: row = %s' % row)
            result.extend(self._get_climate_sensors_params(climate_sensors))

        if self.temp_sensor_count:
            temp_sensors = yield self._get_temp_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: temp_sensors = %s' %
                        temp_sensors)
            result.extend(self._get_temp_sensors_params(temp_sensors))

        if self.airflow_sensor_count:
            airflow_sensors = yield self.get_airflow_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: airflow_sensors = %s' %
                        airflow_sensors)
            result.extend(self._get_airflow_sensors_params(airflow_sensors))

        if self.door_sensor_count:
            door_sensors = yield self._get_door_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: door_sensors = %s' %
                        door_sensors)
            result.extend(self._get_door_sensors_params(door_sensors))

        if self.water_sensor_count:
            water_sensors = yield self._get_water_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: water_sensors = %s' %
                        water_sensors)
            result.extend(self._get_water_sensors_params(water_sensors))

        if self.current_sensor_count:
            current_sensors = yield self._get_current_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: current_sensors = %s' %
                        current_sensors)
            result.extend(self._get_current_sensors_params(current_sensors))

        if self.millivolt_sensor_count:
            millivolt_sensors = yield self._get_millivolt_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: millivolt_sensors = %s' %
                        millivolt_sensors)
            result.extend(self._get_millivolt_sensors_params(millivolt_sensors))

        if self.dewpoint_sensor_count:
            dewpoint_sensors = yield self._get_dewpoint_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: dewpoint_sensors = %s' %
                        dewpoint_sensors)
            result.extend(self._get_dewpoint_sensors_params(dewpoint_sensors))
        if self.digital_sensor_count:
            digital_sensors = yield self._get_digital_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: digital_sensors = %s' %
                        digital_sensors)
            result.extend(self._get_digital_sensors_params(digital_sensors))

        if self.cpm_sensor_count:
            cpm_sensors = yield self._get_cpm_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: cpm_sensors = %s' %
                        cpm_sensors)
            result.extend(self._get_cpm_sensors_params(cpm_sensors))

        if self.smoke_alarm_sensor_count:
            smoke_sensors = yield self._get_smoke_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: smoke_sensors = %s' %
                        smoke_sensors)
            result.extend(self._get_smoke_sensors_params(smoke_sensors))

        if self.neg48Vdc_sensor_count:
            neg48Vdc_sensors = yield self._get_neg48Vdc_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: neg48Vdc_sensors = %s' %
                        neg48Vdc_sensors)
            result.extend(self._get_neg48Vdc_sensors_params(neg48Vdc_sensors))

        if self.pos30Vdc_sensor_count:
            pos30Vdc_sensors = yield self._get_pos30Vdc_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: pos30Vdc_sensors = %s' %
                        pos30Vdc_sensors)
            result.extend(self._get_pos30Vdc_sensors_params(pos30Vdc_sensors))
        
        if self.analog_sensor_count:
            analog_sensors = yield self._get_analog_sensors()
            self.logger.error(
                    'ItWatchDogsMib:: get_all_sensors: analog_sensors = %s' %
                        analog_sensors)
            result.extend(self._get_analog_sensors_params(analog_sensors))

        defer.returnValue(result)

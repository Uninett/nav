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


class ItWatchDogsMib(mibretriever.MibRetriever):
    from nav.smidumps.itw_mib import MIB as mib

	climate_count = 0
	power_monitor_count = 0
	temp_sensor_count = 0
	airflow_sensor_count = 0
	power_only_count = 0
	door_sensor_count = 0
	water_sensor_count = 0
	current_sensor_count = 0
	millivolt_sensor_count = 0
	power3i_ch_sensor_count = 0
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
	neg48_vdc_sensor_count = 0
	pos30_vdc_sensor_count = 0
	analog_sensor_count = 0


    def get_module_name(self):
        return self.mib.get('moduleName', None)

    def retrieve_std_columns(self):
        return self.retrieve_columns([
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
                    'tempSensorSerial',
                    'tempSensorName',
                    'tempSensorAvail',
                    'tempSensorTempC',
                    #
                    'airFlowSensorSerial',
                    'airFlowSensorName',
                    'airFlowSensorAvail',
                    'airFlowSensorFlow',
                    'airFlowSensorTempC',
                    'airFlowSensorHumidity',
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
                    'doorSensorSerial',
                    'doorSensorName',
                    'doorSensorAvail',
                    'doorSensorStatus',
                    #
                    'waterSensorSerial',
                    'waterSensorName',
                    'waterSensorAvail',
                    'waterSensorDampness',
                    #
                    'currentMonitorSerial',
                    'currentMonitorName',
                    'currentMonitorAvail',
                    'currentMonitorAmps',
                    #
                    'millivoltMonitorSerial',
                    'millivoltMonitorName',
                    'millivoltMonitorAvail',
                    'millivoltMonitorMV',
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
                    'dewPointSensorSerial',
                    'dewPointSensorName',
                    'dewPointSensorAvail',
                    'dewPointSensorDewPoint',
                    'dewPointSensorTempC',
                    'dewPointSensorHumidity',
                    #
                    'digitalSensorSerial',
                    'digitalSensorName',
                    'digitalSensorAvail',
                    'digitalSensorDigital',
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
                    'cpmSensorSerial',
                    'cpmSensorName',
                    'cpmSensorAvail',
                    'cpmSensorStatus',
                    #
                    'smokeAlarmSerial',
                    'smokeAlarmName',
                    'smokeAlarmAvail',
                    'smokeAlarmStatus',
                    #
                    'neg48VdcSensorSerial',
                    'neg48VdcSensorName',
                    'neg48VdcSensorAvail',
                    'neg48VdcSensorVoltage',
                    #
                    'pos30VdcSensorSerial',
                    'pos30VdcSensorName',
                    'pos30VdcSensorAvail',
                    'pos30VdcSensorVoltage',
                    #
                    'analogSensorSerial',
                    'analogSensorName',
                    'analogSensorAvail',
                    'analogSensorAnalog',
                    ])

    def _get_climate_sensors(self):
        df = self.retrieve_columns([
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
        df.addCallback(reduce_index)
        return df

    def _get_climate_sensors_params(self, climate_sensors):
        sensors = []
        for idx, climate_sensor in climate_sensors.items():
            available = climate_sensor.get('climateAvail', None)
            if available:
                climate_sensor_oid = climate_sensor.get(0, None)
                serial = climate_sensor.get('climateSerial', None)

                temp_mib = self.nodes.get('climateTempC', None)
                oid = str(temp_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = 'celsius'
                precision = 0
                scale = ''
                description = 'climateTempC'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })

                humidity_mib = self.nodes.get('climateHumidity', None)
                oid = str(humidity_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = 'percentRH'
                precision = 0
                scale = ''
                description = 'climateHumidity'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })

                airflow_mib = self.nodes.get('climateAirflow', None)
                oid = str(airflow_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = 'airflow'
                precision = 0
                scale = ''
                description = 'climateAirflow'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })

                light_mib = self.nodes.get('climateLight', None)
                oid = str(light_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = ''
                precision = 0
                scale = ''
                description = 'climateLight'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })

                sound_mib = self.nodes.get('climateSound', None)
                oid = str(sound_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = ''
                precision = 0
                scale = ''
                description = 'climateSound'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })

                io1_mib = self.nodes.get('climateIO1', None)
                oid = str(io1_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = ''
                precision = 0
                scale = ''
                description = 'climateIO1'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })

                io2_mib = self.nodes.get('climateIO2', None)
                oid = str(io2_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = ''
                precision = 0
                scale = ''
                description = 'climateIO2'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })

                io3_mib = self.nodes.get('climateIO3', None)
                oid = str(io3_mib.oid) + str(climate_sensor_oid)
                unit_of_measurement = ''
                precision = 0
                scale = ''
                description = 'climateIO3'
                name = description
                internal_name = serial + name
                sensors.append({
                                'oid': oid,
                                'unit_of_measurement': unit_of_measurement,
                                'precision': precision,
                                'scale': scale,
                                'description': description,
                                'name': name,
                                'internal_name': internal_name,
                                'mib': self.get_module_name(),
                                })
        return sensors

    def _get_sensor_count(self):
        df = self.retrieve_columns([
                    'climateCount',
                    'powerMonitorCount',
                    'tempSensorCount',
                    'airflowSensorCount',
                    'powerOnlyCount',
                    'doorSensorCount',
                    'waterSensorCount',
                    'currentSensorCount',
                    'millivoltSensorCount',
                    'power3ChSensorCount',
                    'outletCount',
                    'vsfcCount',
                    'ctrl3ChCount',
                    'ctrlGrpAmpsCount',
                    'ctrlOutputCount',
                    'dewpointSensorCount',
                    'digitalSensorCount',
                    'dstsSensorCount',
                    'cpmSensorCount',
                    'smokeAlarmSensorCount',
                    'neg48VdcSensorCount',
                    'pos30VdcSensorCount',
                    'analogSensorCount',
                    ])
        df.addCallback(reduce_index)
        return df

    def _set_sensor_count(self, sensor_count):
        self.logger.error('_set_sensor_count: %s' % sensor_count)
        self.climate_count = sensor_count.get('climateCount', 0)
        self.power_monitor_count = sensor_count.get('powerMonitorCount', 0)
        self.temp_sensor_count = sensor_count.get('tempSensorCount', 0)
        self.airflow_sensor_count = sensor_count.get(
                                        'airflowSensorCount', 0)
        self.power_only_count = sensor_count.get('powerOnlyCount', 0)
        self.door_sensor_count = sensor_count.get('doorSensorCount', 0)
        self.water_sensor_count = sensor_count.get('waterSensorCount', 0)
        self.current_sensor_count = sensor_count.get('currentSensorCount', 0)
        self.millivolt_sensor_count = sensor_count.get(
                                                'millivoltSensorCount', 0)
        self.power3i_ch_sensor_count = sensor_count.get(
                                                'power3ChSensorCount', 0)
        self.outlet_count = sensor_count.get('outletCount', 0)
        self.vsfc_count = sensor_count.get('vsfcCount', 0)
        self.ctrl3_ch_count = sensor_count.get('ctrl3ChCount', 0)
        self.ctrl_grp_amps_count = sensor_count.get('ctrlGrpAmpsCount', 0)
        self.ctrl_output_count = sensor_count.get('ctrlOutputCount', 0)
        self.dewpoint_sensor_count = sensor_count.get('dewpointSensorCount', 0)
        self.digital_sensor_count = sensor_count.get('digitalSensorCount', 0)
        self.dsts_sensor_count = sensor_count.get('dstsSensorCount', 0)
        self.cpm_sensor_count = sensor_count.get('cpmSensorCount', 0)
        self.smoke_alarm_sensor_count = sensor_count.get(
                                                    'smokeAlarmSensorCount', 0)
        self.neg48_vdc_sensor_count = sensor_count.get(
                                                    'neg48VdcSensorCount', 0)
        self.pos30_vdc_sensor_count = sensor_count.get(
                                                    'pos30VdcSensorCount', 0)
        self.analog_sensor_count = sensor_count.get('analogSensorCount', 0)
        return None

    @defer.inlineCallbacks
    def get_all_sensors(self):
        sensor_count = yield self._get_sensor_count()
        self._set_sensor_count(sensor_count)
        self.logger.debug('ItWatchDogsMib:: get_all_sensors: ip = %s' %
                            self.agent_proxy.ip)

        result = []
        if self.climate_count:
            climate_sensors = yield self._get_climate_sensors()
            self.logger.debug(
                'ItWatchDogsMib:: get_all_sensors: climate_sensors = %s' %
                    climate_sensors)
            for row_id, row in climate_sensors.items():
                self.logger.debug('ItWatchDogsMib:: get_all_sensors: row = %s' %
                                row)
            result.extend(self._get_climate_sensors_params(climate_sensors))
        defer.returnValue(result)

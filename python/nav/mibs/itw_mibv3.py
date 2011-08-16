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

class ItWatchDogsMibV3(mibretriever.MibRetriever):
    from nav.smidumps.itw_mibv3 import MIB as mib

    oid_name_map = dict((OID(attrs['oid']), name)
                        for name, attrs in mib['nodes'].items())

    lowercase_nodes = dict((key.lower(), key)
                            for key in mib['nodes'])

    def get_module_name(self):
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
                                serial, 'climateHumidity',
                                u_o_m='percentRH', name=name))

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

                sensors.append(self._make_result_dict(climate_oid,
                                self.nodes.get('climateDewPointC', None),
                                serial, 'climateDewPointC', u_o_m="celsius",
                                name=name))
        return sensors

    @for_table('powMonTable')
    def _get_pow_mon_sensors_params(self, pow_mon_sensors):
        sensors = []
        for idx, pow_mon_sensor in pow_mon_sensors.items():
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
                                self.nodes.get('powMonDeciAmps', None), serial,
                                'powMonDeciAmps', u_o_m='amperes', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonRealPower', None), serial,
                                'powMonRealPower', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonApparentPower', None),
                                serial, 'powMonApparentPower', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonPowerFactor', None),
                                serial, 'powMonPowerFactor', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonOutlet1', None), serial,
                                'powMonOutlet1', name=name))
                sensors.append(self._make_result_dict(pow_mon_oid,
                                self.nodes.get('powMonOutlet2', None), serial,
                                'powMonOutlet2', name=name))
        return sensors


    @for_table('tempSensorTable')
    def _get_temp_sensors_params(self, temp_sensors):
        sensors = []
        for idx, temp_sensor in temp_sensors.items():
            temp_avail = temp_sensor.get('tempSensorAvail', None)
            if temp_avail:
                temp_oid = temp_sensor.get(0, None)
                serial = temp_sensor.get('tempSensorSerial', None)
                name = temp_sensor.get('tempSensorName', None)
                sensors.append(self._make_result_dict(temp_oid,
                                self.nodes.get('tempSensorTempC', None), serial,
                                'tempSensorTempC', u_o_m='celsius', name=name))
        return sensors
        
    @for_table('airFlowSensorTable')
    def _get_air_flow_sensors_params(self, air_flow_sensors):
        sensors = []
        for idx, air_flow_sensor in air_flow_sensors.items():
            air_flow_avail = air_flow_sensor.get('airFlowSensorAvail', None)
            if air_flow_avail:
                air_flow_oid = air_flow_sensor.get(0, None)
                serial = air_flow_sensor.get('airFlowSensorSerial', None)
                name = air_flow_sensor.get('airFlowSensorName', None)
                sensor.append(self._make_result_dict(air_flow_oid,
                                self.nodes.get('airFlowSensorTempC', None),
                                serial, 'airFlowSensorTempC', u_o_m='celsius',
                                name=name))
                sensor.append(self._make_result_dict(air_flow_oid,
                                self.nodes.get('airFlowSensorFlow', None),
                                serial, 'airFlowSensorFlow', name=name))
                sensor.append(self._make_result_dict(air_flow_oid,
                                self.nodes.get('airFlowSensorHumidity', None),
                                serial, 'airFlowSensorHumidity',
                                u_o_m='percentRH', name=name))
                sensor.append(self._make_result_dict(air_flow_oid,
                                self.nodes.get('airFlowSensorDewPointC', None),
                                serial, 'airFlowSensorDewPointC',
                                u_o_m='celsius', name=name))
        return sensors

    @for_table('powerTable')
    def _get_power_sensors_params(self, power_sensors):
        sensors = []
        for idx, power_sensor in power_sensors.items():
            power_sensor_avail = power_sensor.get('powerAvail', None)
            if power_sensor_avail:
                power_sensor_oid = power_sensor.get(0, None)
                serial = power_sensor.get('powerSerial', None)
                name = powerSerial.get('powerName', None)
                sensor.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerVolts', None), serial,
                                'powerVolts', u_o_m='volts', name=name))
                sensor.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerDeciAmps', None), serial,
                                'powerDeciAmps', u_o_m='amperes', name=name))
                sensor.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerRealPower', None), serial,
                                'powerRealPower', name=name))
                sensor.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerApparentPower', None),
                                serial, 'powerApparentPower', name=name))
                sensor.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerApparentPower', None),
                                serial, 'powerApparentPower', name=name))
                sensor.append(self._make_result_dict(power_sensor_oid,
                                self.nodes.get('powerPowerFactor', None),
                                serial, 'powerPowerFactor', name=name))
        return sensors

    @for_table('doorSensorTable')
    def _get_door_sensors_params(self, door_sensors):
        sensors = []
        for idx, door_sensor in door_sensors.items():
            door_sensor_avail = door_sensor.get('doorSensorAvail', None)
            if door_sensor_avail:
                door_sensor_oid = door_sensor.get(0, None)
                serial = door_sensor.get('doorSensorSerial', None)
                name = doorSensorSerial.get('doorSensorName', None)
                sensor.append(self._make_result_dict(door_sensor_oid,
                                self.nodes.get('doorSensorStatus', None),
                                serial, 'doorSensorStatus', name=name))
        return sensors

    @for_table('waterSensorTable')
    def _get_water_sensors_params(self, water_sensors):
        sensors = []
        for idx, water_sensor in water_sensors.items():
            water_sensor_avail = water_sensor.get('waterSensorAvail', None)
            if water_sensor_avail:
                water_sensor_oid = water_sensor.get(0, None)
                serial = water_sensor.get('waterSensorSerial', None)
                name = water_sensor.get('waterSensorName', None)
                sensor.append(self._make_result_dict(water_sensor_oid,
                                self.nodes.get('waterSensorDampness', None),
                                serial, 'waterSensorSerial', name=name))
        return sensors

    @for_table('currentMonitorTable')
    def _get_current_monitors_params(self, current_monitors):
        sensors = []
        for idx, current_mon in current_monitors.items():
            current_mon_avail = current_mon.get('currentMonitorAvail', None)
            if current_monitor_avail:
                current_mon_oid = current_mon.get(0, None)
                serial = current_mon.get('currentMonitorSerial', None)
                name = current_mon.get('currentMonitorName', None)
                sensors.append(self._make_result_dict(current_mon_oid,
                                self.nodes.get('currentMonitorDeciAmps', None),
                                serial, 'currentMonitorDeciAmps',
                                u_o_m='amperes', name=name))
        return sensors

    @for_table('millivoltMonitorTable')
    def _get_millivolt_monitors_params(self, millivolts_monitors):
        sensors = []
        for idx, mvolts_mon in millivolts_monitors.items():
            mvolts_mon_avail = mvolts_mon.get('millivoltMonitorAvail', None)
            if mvolts_mon_avail:
                mvolts_mon_oid = mvolts_mon.get(0, None)
                serial = mvolts_mon.get('millivoltMonitorSerial', None)
                name = mvolts_mon.get('millivoltMonitorName', None)
                sensors.append(self._make_result_dict(mvolts_mon_oid,
                                self.nodes.get('millivoltMonitorMV', None),
                                serial, 'millivoltMonitorMV', u_o_m='volts',
                                scale='milli', name=name))
        return sensors

    @for_table('pow3ChTable')
    def _get_pow3_ch_params(self, pow3_chs):
        sensors = []
        for idx, pow3_ch in pow3_chs.items():
            pow3_ch_avail = pow3_ch.get('pow3ChAvail', None)
            if pow3_ch_avail:
                pow3_ch_oid = pow3_ch.get(0, None)
                serial = pow3_ch.get('pow3ChSerial', None)
                name = pow3_ch.get('pow3ChName', None)
                # sensors iwith postfix A - C
                ports = [chr(i) for i in xrange(ord('A'),ord('D'))]
                for port in ports:
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChKWattHrs' + port, None),
                            serial, 'pow3ChKWattHrs' + port, name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChVolts' + port, None),
                            serial, 'pow3ChVolts' + port, u_o_m='volts',
                            name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChDeciAmps' + port, None),
                            serial, 'pow3ChVoltMax' + port, u_o_m='amperes',
                            name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChVoltMin' + port, None),
                            serial, 'pow3ChVoltMin' + port, u_o_m='volts',
                            name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChVoltPeak' + port, None),
                            serial, 'pow3ChVoltPeak' + port, u_o_m='volts',
                            name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChDeciAmps' + port, None),
                            serial, 'pow3ChDeciAmps' + port, u_o_m='amperes',
                            name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChRealPower' + port, None),
                            serial, 'pow3ChRealPower' + port, name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChApparentPower' + port, None),
                            serial, 'pow3ChApparentPower' + port, name=name))
                    sensors.append(self._make_result_dict(pow3_ch_oid,
                            self.nodes.get('pow3ChPowerFactor' + port, None),
                            serial, 'pow3ChPowerFactor' + port, name=name))
        return sensors

    @for_table('outletTable')
    def _get_outlet_params(self, outlets):
        sensors = []
        for idx, outlet in outlets.items():
            outlet_avail = outlet.get('outletAvail', None)
            if outlet_avail:
                outlet_oid = outlet.get(0, None)
                serial = outlet.get('outletSerial', None)
                name = outlet.get('outletName', None)
                sensors.append(self._make_result_dict(outlet_oid,
                                self.nodes.get('outlet1Status', None), serial,
                                'outlet1Status', name=name))
                sensors.append(self._make_result_dict(outlet_oid,
                                self.nodes.get('outlet2Status', None), serial,
                                'outlet2Status', name=name))
        return sensors

    @for_table('vsfcTable')
    def _get_vsfc_params(self, vsfcs):
        sensors = []
        for idx, vsfc in vsfcs.items():
            vsfc_avail = vsfc.get('vsfcAvail', None)
            if vsfc_avail:
                vsfc_oid = vsfc.get(0, None)
                serial = vsfc.get('vsfcSerial', None)
                name = vsfc.get('vsfcName', None)
                sensors.append(self._make_result_dict(vsfc_oid,
                                self.nodes.get('vsfcSetPointC', None), serial,
                                'vsfcSetPointC', u_o_m='celsius', name=name))
                sensors.append(self._make_result_dict(vsfc_oid,
                                self.nodes.get('vsfcFanSpeed', None), serial,
                                'vsfcFanSpeed', u_o_m='rpm', name=name))
                sensors.append(self._make_result_dict(vsfc_oid,
                                self.nodes.get('vsfcIntTempC', None), serial,
                                'vsfcIntTempC', u_o_m='celsius', name=name))
                # sensors for ports 1 - 4
                for port in range(1, 5):
                    sensor_key = 'vsfcExt' + str(port) + 'TempC'
                    sensors.append(self._make_result_dict(vsfc_oid,
                                self.nodes.get(sensor_key, None), serial,
                                sensor_key, u_o_m='celsius', name=name))
        return sensors

    @for_table('ctrl3ChTable')
    def _get_ctrl3_ch_params(self, ctrl3_chs):
        sensors = []
        for idx, in ctrl3_ch in ctrl3_chs.items():
            ctrl3_ch_avail = ctrl3_ch.get('ctrl3ChAvail', None)
            if ctrl3_ch_avail:
                ctrl3_ch_oid = ctrl3_ch.get(0, None)
                serial = ctrl3_ch.get('ctrl3ChSerial', None)
                name = ctrl3_ch.get('ctrl3ChName', None)
                # sensors A - C
                postfixes = [chr(i) for i in xrange(ord('A'),ord('D'))]
                for pfix in postfixes:
                    sensor.append(self._make_result_dict(ctrl3_ch_oid,
                                    self.nodes.get('ctrl3ChVolts' + pfix, None),
                                    serial, 'ctrl3ChVolts' + pfix,
                                    u_o_m='volts', name=name))
                    sensor.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChVoltPeak' + pfix, None),
                                serial, 'ctrl3ChVoltPeak' + pfix, u_o_m='volts',
                                name=name))
                    sensor.append(self._make_result_dict(ctrl3_ch_oid,
                                self.nodes.get('ctrl3ChDeciAmps' + pfix, None),
                                serial, 'ctrl3ChDeciAmps' + pfix,
                                u_o_m='amperes', name=name))
                    sensor.append(self._make_result_dict(ctrl3_ch_oid,
                        self.nodes.get('ctrl3ChDeciAmpsPeak' + pfix, None),
                        serial, 'ctrl3ChDeciAmpsPeak' + pfix, u_o_m='amperes',
                        name=name))
                    sensor.append(self._make_result_dict(ctrl3_ch_oid,
                        self.nodes.get('ctrl3ChRealPower' + pfix, None),
                        serial, 'ctrl3ChRealPower' + pfix, name=name))
                    sensor.append(self._make_result_dict(ctrl3_ch_oid,
                        self.nodes.get('ctrl3ChApparentPower' + pfix, None),
                        serial, 'ctrl3ChApparentPower' + pfix, name=name))
                    sensor.append(self._make_result_dict(ctrl3_ch_oid,
                        self.nodes.get('ctrl3ChPowerFactor' + pfix, None),
                        serial, 'ctrl3ChPowerFactor' + pfix, name=name))
        return sensors

    @for_table('ctrlGrpAmpsTable')
    def _get_ctrl_grp_amps_params(self, ctrl_grp_amps):
        sensors = []
        for idx, ctrl_grp_amp in ctrl_grp_amps.items():
            ctrl_grp_amp_avail = ctrl_grp_amp.get('ctrlGrpAmpsAvail', None)
            if ctrl_grp_amp_avail:
                ctrl_grp_amp_oid = ctrl_grp_amp.get(0, None)
                serial = ctrl_grp_amp.get('ctrlGrpAmpsSerial', None)
                name = ctrl_grp_amp_avail.get('ctrlGrpAmpsName', None)
                postfixes = [chr(i) for i in xrange(ord('A'),ord('I'))]
                for pfix in postfixes:
                    sensor.append(self._make_result_dict(ctrl_grp_amp_oid,
                            self.nodes.get('ctrlGrpAmps' + pfix, None), serial,
                            'ctrlGrpAmps' + pfix, u_o_m='amperes', name=name))
                    sensor.append(self._make_result_dict(ctrl_grp_amp_oid,
                        self.nodes.get('ctrlGrpAmps' + pfix + 'Volts', None),
                        serial, 'ctrlGrpAmps' + pfix + 'AVolts', name=name))
        return sensors

    @for_table('ctrlOutletTable')
    def _get_ctrl_outlet_params(self, ctrl_outlets):
        sensors = []
        for idx, ctrl_outlet in ctrl_outlets.items():
            ctrl_outlet_oid = ctrl_outlet.get(0, None)
            serial = ctrl_outlet.get('ctrlOutletIndex', None),
            group = ctrl_outlet.get('ctrlOutletGroup', None)
            name = group + ': ' + ctrl_outlet.get('ctrlOutletName', None)
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletStatus', None), serial,
                        'ctrlOutletStatus', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletFeedback', None), serial,
                        'ctrlOutletFeedback', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletPending', None), serial,
                        'ctrlOutletPending', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletDeciAmps', None), serial,
                        'ctrlOutletDeciAmps', u_o_m='amperes', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletUpDelay', None), serial,
                        'ctrlOutletUpDelay', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletDwnDelay', None), serial,
                        'ctrlOutletDwnDelay', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletRbtDelay', None), serial,
                        'ctrlOutletRbtDelay', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletPOAAction', None), serial,
                        'ctrlOutletPOAAction', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletPOADelay', None), serial,
                        'ctrlOutletPOADelay', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletKWattHrs', None), serial,
                        'ctrlOutletKWattHrs', name=name))
            sensors.append(self._make_result_dict(ctrl_outlet_oid,
                        self.nodes.get('ctrlOutletPower', None), serial,
                        'ctrlOutletPower', name=name))
        return sensors

    @for_table('dewPointSensorTable')
    def _get_dewpoint_sensors_params(self, dewpoint_sensors):
        sensors = []
        for idx, dewpoint_sensor in dewpoint_sensors.items():
            dewpoint_sensor_avail = dewpoint_sensor.get('dewPointSensorAvail',
                                                            None)
            if dewpoint_sensor_avail:
                dewpoint_sensor_oid = dewpoint_sensor.get(0, None)
                serial = dewpoint_sensor.get('dewPointSensorSerial', None)
                name = dewpoint_sensor.get('dewPointSensorName', None)
                sensor.append(self._make_result_dict(dewpoint_sensor_oid,
                                self.nodes.get('dewPointSensorTempC', None),
                                serial, 'dewPointSensorTempC', u_o_m='celsius',
                                name=name))
                sensor.append(self._make_result_dict(dewpoint_sensor_oid,
                                self.nodes.get('dewPointSensorHumidity', None),
                                serial, 'dewPointSensorHumidity',
                                u_o_m='percentRH', name=name))
                sensor.append(self._make_result_dict(dewpoint_sensor_oid,
                                self.nodes.get('dewPointSensorDewPointC', None),
                                serial, 'dewPointSensorDewPointC',
                                u_o_m='celsius', name=name))
        return sensors

    @for_table('digitalSensorTable')
    def _get_digital_sensors_params(self, digital_sensors):
        sensors = []
        for idx, digital_sensor in digital_sensors.items():
            digital_avail = digital_sensor.get('digitalSensorAvail', None)
            if digital_avail:
                digital_sensor_oid = digital_sensor.get(0, None)
                serial = digital_sensor.get('digitalSensorSerial', None)
                name = digital_sensor.get('digitalSensorName', None)
                sensor.append(self._make_result_dict(digital_sensor_oid,
                                self.nodes.get('digitalSensorDigital', None),
                                serial, 'digitalSensorDigital', name=name))
        return sensors

    @for_table('dstsTable')
    def _get_dsts_params(self, dsts_sensors):
        sensors = []
        for idx, dsts_sensor in dsts_sensors.items():
            dsts_sensor_avail = dsts_sensor.get('dstsAvail', None)
            if dsts_sensor_avail:
                dsts_sensor_oid = dsts_sensor.get(0, None)
                serial = dsts_sensor.get('dstsSerial', None)
                name = dsts_sensor.get('dstsName', None)
                postfixes = [chr(i) for i in xrange(ord('A'),ord('C'))]
                for pfix in postfixes:
                    sensor.append(self._make_result_dict(dsts_sensor_oid,
                            self.nodes.get('dstsVolts' + pfix, None), serial,
                            'dstsVolts' + pfix, u_o_m='volts', name=name))
                    sensor.append(self._make_result_dict(dsts_sensor_oid,
                            self.nodes.get('dstsDeciAmps' + pfix, None), serial,
                            'dstsDeciAmps' + pfix, u_o_m='amperes', name=name))
                    sensor.append(self._make_result_dict(dsts_sensor_oid,
                           self.nodes.get('dstsSource' + pfix + 'Active', None),
                           serial, 'dstsSource' + pfix + 'Active', name=name))
                    sensor.append(self._make_result_dict(dsts_sensor_oid,
                            self.nodes.get('dstsPowerStatus' + pfix, None),
                            serial, 'dstsPowerStatus' + pfix, name=name))
                    sensor.append(self._make_result_dict(dsts_sensor_oid,
                            self.nodes.get('dstsSource' + pfix + 'TempC', None),
                            serial, 'dstsSource' + pfix + 'TempC',
                            u_o_m='celsius', name=name))
        return sensors

    @for_table('cpmSensorTable')
    def _get_cpm_params(self, cpm_sensors):
        sensors = []
        for idx, cpm_sensor in cpm_sensors.items():
            cpm_sensor_avail = cpm_sensor.get('cpmSensorAvail', None)
            if cpm_sensor_avail:
                cpm_sensor_oid = cpm_sensor.get(0, None)
                serial = cpm_sensor.get('cpmSensorSerial', None)
                name = cpm_sensor.get('cpmSensorName', None)
                sensor.append(self._make_result_dict(cpm_sensor_oid,
                                self.nodes.get('cpmSensorStatus', None), serial,
                                'cpmSensorStatus', name=name))
        return sensors

    @for_table('smokeAlarmTable')
    def _get_smoke_alarms_params(self, smoke_alarms):
        sensors = []
        for idx, smoke_alarm in smoke_alarms.items():
            smoke_alarm_avail = smoke_alarm.get('smokeAlarmAvail', None)
            if smoke_alarm_avail:
                smoke_alarm_oid = smoke_alarm.get(0, None)
                serial = smoke_alarm.get('smokeAlarmSerial', None)
                name = smoke_alarm.get('smokeAlarmName', None)
                sensor.append(self._make_result_dict(smoke_alarm_oid,
                                self.nodes.get('smokeAlarmStatus', None),
                                serial, 'smokeAlarmStatus', name=name))
        return sensors

    @for_table('neg48VdcSensorTable')
    def _get_neg48vdc_sensors_params(self, neg48vdc_sensors):
        sensors = []
        for idx, neg48vdc_sensor in neg48vdc_sensors.items():
            neg48vdc_sensor_avail = neg48vdc_sensor.get('neg48VdcSensorAvail',
                                                             None)
            if neg48vdc_sensor_avail:
                neg48vdc_sensor_oid = neg48vdc_sensor.get(0, None)
                serial = neg48vdc_sensor.get('neg48VdcSensorSerial', None)
                name = neg48vdc_sensor.get('neg48VdcSensorName', None)
                sensors.append(self._make_result_dict(neg48vdc_sensor_oid,
                                self.nodes.get('neg48VdcSensorVoltage', None),
                                serial, 'neg48VdcSensorVoltage',
                                u_o_m='voltsDC', name=name))
        return sensors

    @for_table('pos30VdcSensorTable')
    def _get_pos30vdc_sensors_params(self, pos30vdc_sensors):
        sensors = []
        for idx, pos30vdc_sensor in pos30vdc_sensors.items():
            pos30vdc_sensor_avail = pos30vdc_sensor.get('pos30VdcSensorAvail',
                                                            None)
            if pos30vdc_sensor_avail:
                pos30vdc_sensor_oid = pos30vdc_sensor.get(0, None)
                serial = pos30vdc_sensor.get('pos30VdcSensorSerial', None)
                name = pos30vdc_sensor.get('pos30VdcSensorName', None)
                sensors.append(self._make_result_dict(neg48vdc_sensor_oid,
                        self.nodes.get('pos30VdcSensorVoltage', None), serial,
                        'pos30VdcSensorVoltage', u_o_m='volts', name=name))
        return sensors

    @for_table('analogSensorTable')
    def _get_analog_sensors_params(self, analog_sensors):
        sensors = []
        for idx, analog_sensor in analog_sensors.items():
            analog_avail = analog_sensor.get('analogSensorAvail', None)
            if analog_avail:
                analog_sensor_oid = analog_sensor.get(0, None)
                serial = analog_sensor.get('analogSensorSerial', None)
                name = analog_sensor.get('analogSensorName', None)
                sensors.append(self._make_result_dict(neg48vdc_sensor_oid,
                            self.nodes.get('analogSensorAnalog', None), serial,
                            'analogSensorAnalog', name=name))
        return sensors

    @for_table('ctrl3ChIECTable')
    def _get_ctrl3_chiects_params(self, ctrl3_chiects):
        sensors = []
        for idx, ctrl3_chiect in ctrl3_chiects.items():
            ctrl3_chiect_avail = ctrl3_chiect.get('ctrl3ChIECAvail', None)
            if ctrl3_chiect_avail:
                ctrl3_chiect_oid = ctrl3_chiect.get(0, None)
                serial = ctrl3_chiect.get('ctrl3ChIECSerial', None)
                name = ctrl3_chiect.get('ctrl3ChIECName', None)
                postfixes = [chr(i) for i in xrange(ord('A'),ord('D'))]
                for pfix in postfixes:
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                            self.nodes.get('ctrl3ChIECKWattHrs' + pfix, None),
                            serial, 'ctrl3ChIECKWattHrs' + pfix, name=name))
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                            self.nodes.get('ctrl3ChIECVolts' + pfix, None),
                            serial, 'ctrl3ChIECVolts' + pfix, u_o_m='volts',
                            name=name))
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                            self.nodes.get('ctrl3ChIECVoltPeak' + pfix, None),
                            serial, 'ctrl3ChIECVoltPeak' + pfix, u_o_m='volts',
                            name=name))
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                            self.nodes.get('ctrl3ChIECDeciAmps' + pfix, None),
                            serial, 'ctrl3ChIECDeciAmps' + pfix,
                            u_o_m='amperes', name=name))
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                          self.nodes.get('ctrl3ChIECDeciAmpsPeak' + pfix, None),
                          serial, 'ctrl3ChIECDeciAmpsPeak' + pfix,
                          u_o_m='amperes', name=name))
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                            self.nodes.get('ctrl3ChIECRealPower' + pfix, None),
                            serial, 'ctrl3ChIECRealPower' + pfix, name=name))
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                         self.nodes.get('ctrl3ChIECApparentPower' + pfix, None),
                         serial, 'ctrl3ChIECApparentPower' + pfix,name=name))
                    sensors.append(self._make_result_dict(ctrl3_chiect_oid,
                           self.nodes.get('ctrl3ChIECPowerFactor' + pfix, None),
                           serial, 'ctrl3ChIECPowerFactor' + pfix, name=name))
        return sensors

    @for_table('climateRelayTable')
    def _get_climate_relays_params(self, climate_relays):
        sensors = []
        for idx, climate_relay in climate_relays.items():
            climate_relay_avail = climate_relay.get('climateRelayAvail', None)
            if climate_relay_avail:
                climate_relay_oid = climate_relay.get(0, None)
                serial = climate_relay.get('climateRelaySerial', None)
                name = climate_relay.get('climateRelayName', None)
                sensors.append(self._make_result_dict(climate_relay_oid,
                                self.nodes.get('climateRelayTempC', None),
                                serial, 'climateRelayTempC', u_o_m='celsius',
                                name=name))
                for i in range(1, 7):
                    sensors.append(self._make_result_dict(climate_relay_oid,
                                self.nodes.get('climateRelayIO' + str(i), None),
                                serial, 'climateRelayIO' + str(i), name=name))
        return sensors

    @for_table('ctrlRelayTable')
    def _get_ctrl_relays_params(self, ctrl_relays):
        sensors = []
        for idx, ctrl_relay in ctrl_relays.items():
            ctrl_relay_oid = ctrl_relay.get(0, None)
            serial = ctrl_relay.get('ctrlRelayIndex', None)
            name = ctrl_relay.get('ctrlRelayName', None)
            sensors.append(self._make_result_dict(ctrl_relay_oid,
                                self.nodes.get('ctrlRelayState', None), serial,
                                'ctrlRelayState', name=name))
            sensors.append(self._make_result_dict(ctrl_relay_oid,
                                self.nodes.get('ctrlRelayLatchingMode', None),
                                serial, 'ctrlRelayLatchingMode', name=name))
            sensors.append(self._make_result_dict(ctrl_relay_oid,
                                self.nodes.get('ctrlRelayOverride', None),
                                serial, 'ctrlRelayOverride', name=name))
            sensors.append(self._make_result_dict(ctrl_relay_oid,
                                self.nodes.get('ctrlRelayAcknowledge', None),
                                serial, 'ctrlRelayAcknowledge', name=name))
        return sensors

    @for_table('airSpeedSwitchSensorTable')
    def _get_airspeed_switch_sensors_params(self, airspeed_switch_sensors):
        sensors = []
        for idx, airspeed_sensor in airspeed_switch_sensors.items():
            airspeed_avail = airspeed_sensor.get('airSpeedSwitchSensorAvail',
                                                    None)
            if airspeed_avail:
                airspeed_oid = airspeed_sensor.get(0, None)
                serial = airspeed_sensor.get('airSpeedSwitchSensorSerial', None)
                name = airspeed_sensor.get('airSpeedSwitchSensorName', None)
                sensors.append(self._make_result_dict(airspeed_oid,
                           self.nodes.get('airSpeedSwitchSensorAirSpeed', None),
                           serial, 'airSpeedSwitchSensorAirSpeed', name=name))
        return sensors

    @for_table('powerDMTable')
    def _get_power_dms_params(self, power_dms):
        sensors = []
        for idx, power_dm in power_dms.items():
            power_dm_avail = power_dm.get('powerDMAvail', None)
            if power_dm_avail:
                power_dm_oid = power_dm.get(0, None)
                serial = power_dm.get('powerDMSerial', None)
                name = power_dm.get('powerDMName', None)
                aux_count = power_dm.get('powerDMUnitInfoAuxCount', None)
                for i in range(1, (aux_count + 1)):
                    aux_numb = str(i)
                    aux_name = (name + ' ' +
                                        power_dm.get('powerDMChannelGroup' +
                                                    aux_numb, None))
                    aux_name += ': ' + power_dm_oid.get('powerDMChannelName' +
                                                        aux_numb, None)
                    aux_name += (' - ' +
                                    power_dm_oid.get('powerDMChannelFriendly' +
                                                        aux_numb, None))
                    sensors.append(self._make_result_dict(power_dm_oid,
                             self.nodes.get('powerDMDeciAmps' + aux_numb, None),
                             serial, 'powerDMDeciAmps' + aux_numb,
                             u_o_m='amperes', name=aux_name))
        return sensors

    @for_table('ioExpanderTable')
    def _get_io_expanders_params(self, io_expanders):
        sensors = []
        for idx, io_expander in io_expanders.items():
            io_expander_avail = io_expander.get('ioExpanderAvail', 0)
            if io_expander_avail:
                io_expander_oid = io_expander.get(0, None)
                serial = io_expander.get('ioExpanderSerial', None)
                name = io_expander.get('ioExpanderName', None)
                for i in range(1, 33):
                    exp_numb = str(i)
                    exp_name = (name + ': ' +
                                io_expander.get('ioExpanderFriendlyName' +
                                                    exp_numb, None))
                    sensors.append(self._make_result_dict(io_expander_oid,
                        self.nodes.get('ioExpanderIO' + exp_numb, None),
                        serial, 'ioExpanderIO' + exp_numb, name=exp_name))
                for i in range(1, 4):
                    relay_numb = str(i)
                    relay_name = (name + ': ' +
                                       io_expander.get('ioExpanderRelayName' +
                                                            relay_numb, None))
                    sensors.append(self._make_result_dict(io_expander_oid,
                                self.nodes.get('ioExpanderRelayState' +
                                                        relay_numb, None),
                                serial, 'ioExpanderRelayState' + relay_numb,
                                name=relay_name))
                    sensors.append(self._make_result_dict(io_expander_oid,
                            self.nodes.get('ioExpanderRelayLatchingMode' +
                                                relay_numb, None),
                            serial, 'ioExpanderRelayLatchingMode' + relay_numb,
                            name=relay_name))
                    sensors.append(self._make_result_dict(io_expander_oid,
                                self.nodes.get('ioExpanderRelayOverride' +
                                                        relay_numb, None),
                                serial, 'ioExpanderRelayOverride' + relay_numb,
                                name=relay_name))
                    sensors.append(self._make_result_dict(io_expander_oid,
                              self.nodes.get('ioExpanderRelayAcknowledge' +
                                                        relay_numb, None),
                              serial, 'ioExpanderRelayAcknowledge' + relay_numb,
                              name=relay_name))
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
        self.logger.error('ItWatchDogsMib:: _get_sensor_count: result = %s',
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
            self.logger.error('ItWatchDogsMib:: get_all_sensors: table = %s',
                                    table)
            sensors = yield self.retrieve_table(table).addCallback(reduce_index)
            self.logger.error('ItWatchDogsMib:: get_all_sensors: %s = %s',
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

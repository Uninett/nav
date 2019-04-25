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
"""
A class that tries to retrieve all sensors from WeatherGoose II.

Uses the vendor-specifica IT-WATCHDOGS-MIB-V3 to detect and collect
sensor-information.
"""
from django.utils.six import itervalues
from twisted.internet import defer

from nav.mibs import reduce_index
from nav.smidumps import get_mib
from nav.mibs import mibretriever
from nav.models.manage import Sensor
from nav.oids import OID

from .itw_mib import for_table


class ItWatchDogsMibV3(mibretriever.MibRetriever):
    """A class that tries to retrieve all sensors from WeatherGoose II"""
    mib = get_mib('IT-WATCHDOGS-MIB-V3')

    oid_name_map = dict((OID(attrs['oid']), name)
                        for name, attrs in mib['nodes'].items())

    lowercase_nodes = dict((key.lower(), key)
                           for key in mib['nodes'])

    def _debug(self, msg, *args, **kwargs):
        return self._logger.debug(self.__class__.__name__ + ":: " + msg,
                                  *args, **kwargs)

    def _error(self, msg, *args, **kwargs):
        return self._logger.error(self.__class__.__name__ + ":: " + msg,
                                  *args, **kwargs)

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
            available = climate_sensor.get('climateAvail', None)
            if available:
                climate_oid = climate_sensor.get(0, None)
                serial = climate_sensor.get('climateSerial', None)
                name = climate_sensor.get('climateName', None)

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

                sensors.append(self._make_result_dict(
                    climate_oid,
                    self._get_oid_for_sensor('climateDewPointC'),
                    serial, 'climateDewPointC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
        return sensors

    @for_table('powMonTable')
    def _get_pow_mon_sensors_params(self, pow_mon_sensors):
        sensors = []
        for pow_mon_sensor in itervalues(pow_mon_sensors):
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
                    self._get_oid_for_sensor('powMonDeciAmps'),
                    serial, 'powMonDeciAmps', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonRealPower'),
                    serial, 'powMonRealPower', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonApparentPower'),
                    serial, 'powMonApparentPower', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonPowerFactor'),
                    serial, 'powMonPowerFactor', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonOutlet1'),
                    serial, 'powMonOutlet1', name=name))
                sensors.append(self._make_result_dict(
                    pow_mon_oid,
                    self._get_oid_for_sensor('powMonOutlet2'),
                    serial, 'powMonOutlet2', name=name))
        return sensors

    @for_table('tempSensorTable')
    def _get_temp_sensors_params(self, temp_sensors):
        sensors = []
        for temp_sensor in itervalues(temp_sensors):
            temp_avail = temp_sensor.get('tempSensorAvail', None)
            if temp_avail:
                temp_oid = temp_sensor.get(0, None)
                serial = temp_sensor.get('tempSensorSerial', None)
                name = temp_sensor.get('tempSensorName', None)
                sensors.append(self._make_result_dict(
                    temp_oid,
                    self._get_oid_for_sensor('tempSensorTempC'),
                    serial, 'tempSensorTempC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
        return sensors

    @for_table('airFlowSensorTable')
    def _get_air_flow_sensors_params(self, air_flow_sensors):
        sensors = []
        for air_flow_sensor in itervalues(air_flow_sensors):
            air_flow_avail = air_flow_sensor.get('airFlowSensorAvail', None)
            if air_flow_avail:
                air_flow_oid = air_flow_sensor.get(0, None)
                serial = air_flow_sensor.get('airFlowSensorSerial', None)
                name = air_flow_sensor.get('airFlowSensorName', None)
                sensors.append(self._make_result_dict(
                    air_flow_oid,
                    self._get_oid_for_sensor('airFlowSensorTempC'),
                    serial, 'airFlowSensorTempC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    air_flow_oid,
                    self._get_oid_for_sensor('airFlowSensorFlow'),
                    serial, 'airFlowSensorFlow', name=name))
                sensors.append(self._make_result_dict(
                    air_flow_oid,
                    self._get_oid_for_sensor('airFlowSensorHumidity'),
                    serial, 'airFlowSensorHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY, name=name))
                sensors.append(self._make_result_dict(
                    air_flow_oid,
                    self._get_oid_for_sensor('airFlowSensorDewPointC'),
                    serial, 'airFlowSensorDewPointC',
                    u_o_m=Sensor.UNIT_CELSIUS, name=name))
        return sensors

    @for_table('powerTable')
    def _get_power_sensors_params(self, power_sensors):
        sensors = []
        for power_sensor in itervalues(power_sensors):
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
                    self._get_oid_for_sensor('powerDeciAmps'),
                    serial, 'powerDeciAmps', u_o_m=Sensor.UNIT_AMPERES,
                    name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerRealPower'),
                    serial, 'powerRealPower', name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerApparentPower'),
                    serial, 'powerApparentPower', name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerApparentPower'),
                    serial, 'powerApparentPower', name=name))
                sensors.append(self._make_result_dict(
                    power_sensor_oid,
                    self._get_oid_for_sensor('powerPowerFactor'),
                    serial, 'powerPowerFactor', name=name))
        return sensors

    @for_table('doorSensorTable')
    def _get_door_sensors_params(self, door_sensors):
        sensors = []
        for door_sensor in itervalues(door_sensors):
            door_sensor_avail = door_sensor.get('doorSensorAvail', None)
            if door_sensor_avail:
                door_sensor_oid = door_sensor.get(0, None)
                serial = door_sensor.get('doorSensorSerial', None)
                name = door_sensor.get('doorSensorName', None)
                sensors.append(self._make_result_dict(
                    door_sensor_oid,
                    self._get_oid_for_sensor('doorSensorStatus'),
                    serial, 'doorSensorStatus', name=name))
        return sensors

    @for_table('waterSensorTable')
    def _get_water_sensors_params(self, water_sensors):
        sensors = []
        for water_sensor in itervalues(water_sensors):
            water_sensor_avail = water_sensor.get('waterSensorAvail', None)
            if water_sensor_avail:
                water_sensor_oid = water_sensor.get(0, None)
                serial = water_sensor.get('waterSensorSerial', None)
                name = water_sensor.get('waterSensorName', None)
                sensors.append(self._make_result_dict(
                    water_sensor_oid,
                    self._get_oid_for_sensor('waterSensorDampness'),
                    serial, 'waterSensorSerial', name=name))
        return sensors

    @for_table('currentMonitorTable')
    def _get_current_monitors_params(self, current_monitors):
        sensors = []
        for current_mon in itervalues(current_monitors):
            current_mon_avail = current_mon.get('currentMonitorAvail', None)
            if current_mon_avail:
                current_mon_oid = current_mon.get(0, None)
                serial = current_mon.get('currentMonitorSerial', None)
                name = current_mon.get('currentMonitorName', None)
                sensors.append(self._make_result_dict(
                    current_mon_oid,
                    self._get_oid_for_sensor('currentMonitorDeciAmps'),
                    serial, 'currentMonitorDeciAmps',
                    u_o_m=Sensor.UNIT_AMPERES, name=name))
        return sensors

    @for_table('millivoltMonitorTable')
    def _get_millivolt_monitors_params(self, millivolts_monitors):
        sensors = []
        for mvolts_mon in itervalues(millivolts_monitors):
            mvolts_mon_avail = mvolts_mon.get('millivoltMonitorAvail', None)
            if mvolts_mon_avail:
                mvolts_mon_oid = mvolts_mon.get(0, None)
                serial = mvolts_mon.get('millivoltMonitorSerial', None)
                name = mvolts_mon.get('millivoltMonitorName', None)
                sensors.append(self._make_result_dict(
                    mvolts_mon_oid,
                    self._get_oid_for_sensor('millivoltMonitorMV'),
                    serial, 'millivoltMonitorMV', u_o_m=Sensor.UNIT_VOLTS_DC,
                    scale='milli', name=name))
        return sensors

    @for_table('pow3ChTable')
    def _get_pow3_ch_params(self, pow3_chs):
        sensors = []
        for pow3_ch in itervalues(pow3_chs):
            pow3_ch_avail = pow3_ch.get('pow3ChAvail', None)
            if pow3_ch_avail:
                pow3_ch_oid = pow3_ch.get(0, None)
                serial = pow3_ch.get('pow3ChSerial', None)
                name = pow3_ch.get('pow3ChName', None)
                # sensors iwith postfix A - C
                ports = [chr(i) for i in range(ord('A'), ord('D'))]
                for port in ports:
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChKWattHrs' + port),
                        serial, 'pow3ChKWattHrs' + port, name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChVolts' + port),
                        serial, 'pow3ChVolts' + port,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChDeciAmps' + port),
                        serial, 'pow3ChVoltMax' + port,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChVoltMin' + port),
                        serial, 'pow3ChVoltMin' + port,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChVoltPeak' + port),
                        serial, 'pow3ChVoltPeak' + port,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChDeciAmps' + port),
                        serial, 'pow3ChDeciAmps' + port,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChRealPower' + port),
                        serial, 'pow3ChRealPower' + port, name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChApparentPower' + port),
                        serial, 'pow3ChApparentPower' + port, name=name))
                    sensors.append(self._make_result_dict(
                        pow3_ch_oid,
                        self._get_oid_for_sensor('pow3ChPowerFactor' + port),
                        serial, 'pow3ChPowerFactor' + port, name=name))
        return sensors

    @for_table('outletTable')
    def _get_outlet_params(self, outlets):
        sensors = []
        for outlet in itervalues(outlets):
            outlet_avail = outlet.get('outletAvail', None)
            if outlet_avail:
                outlet_oid = outlet.get(0, None)
                serial = outlet.get('outletSerial', None)
                name = outlet.get('outletName', None)
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
    def _get_vsfc_params(self, vsfcs):
        sensors = []
        for vsfc in itervalues(vsfcs):
            vsfc_avail = vsfc.get('vsfcAvail', None)
            if vsfc_avail:
                vsfc_oid = vsfc.get(0, None)
                serial = vsfc.get('vsfcSerial', None)
                name = vsfc.get('vsfcName', None)
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
    def _get_ctrl3_ch_params(self, ctrl3_chs):
        sensors = []
        for ctrl3_ch in itervalues(ctrl3_chs):
            ctrl3_ch_avail = ctrl3_ch.get('ctrl3ChAvail', None)
            if ctrl3_ch_avail:
                ctrl3_ch_oid = ctrl3_ch.get(0, None)
                serial = ctrl3_ch.get('ctrl3ChSerial', None)
                name = ctrl3_ch.get('ctrl3ChName', None)
                # sensors A - C
                postfixes = [chr(i) for i in range(ord('A'), ord('D'))]
                for pfix in postfixes:
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChVolts' + pfix),
                        serial, 'ctrl3ChVolts' + pfix,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChVoltPeak' + pfix),
                        serial, 'ctrl3ChVoltPeak' + pfix,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChDeciAmps' + pfix),
                        serial, 'ctrl3ChDeciAmps' + pfix,
                        u_o_m=Sensor.UNIT_AMPERES, name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChDeciAmpsPeak' + pfix),
                        serial, 'ctrl3ChDeciAmpsPeak' + pfix,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChRealPower' + pfix),
                        serial, 'ctrl3ChRealPower' + pfix, name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChApparentPower' + pfix),
                        serial, 'ctrl3ChApparentPower' + pfix, name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_ch_oid,
                        self._get_oid_for_sensor('ctrl3ChPowerFactor' + pfix),
                        serial, 'ctrl3ChPowerFactor' + pfix, name=name))
        return sensors

    @for_table('ctrlGrpAmpsTable')
    def _get_ctrl_grp_amps_params(self, ctrl_grp_amps):
        sensors = []
        for ctrl_grp_amp in itervalues(ctrl_grp_amps):
            ctrl_grp_amp_avail = ctrl_grp_amp.get('ctrlGrpAmpsAvail', None)
            if ctrl_grp_amp_avail:
                ctrl_grp_amp_oid = ctrl_grp_amp.get(0, None)
                serial = ctrl_grp_amp.get('ctrlGrpAmpsSerial', None)
                name = ctrl_grp_amp_avail.get('ctrlGrpAmpsName', None)
                postfixes = [chr(i) for i in range(ord('A'), ord('I'))]
                for pfix in postfixes:
                    sensors.append(self._make_result_dict(
                        ctrl_grp_amp_oid,
                        self._get_oid_for_sensor('ctrlGrpAmps' + pfix),
                        serial, 'ctrlGrpAmps' + pfix, u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl_grp_amp_oid,
                        self._get_oid_for_sensor('ctrlGrpAmps' + pfix + 'Volts'),
                        serial, 'ctrlGrpAmps' + pfix + 'AVolts', name=name))
        return sensors

    @for_table('ctrlOutletTable')
    def _get_ctrl_outlet_params(self, ctrl_outlets):
        sensors = []
        for ctrl_outlet in itervalues(ctrl_outlets):
            ctrl_outlet_oid = ctrl_outlet.get(0, None)
            serial = ctrl_outlet.get('ctrlOutletIndex', None),
            group = ctrl_outlet.get('ctrlOutletGroup', None)
            name = group + ': ' + ctrl_outlet.get('ctrlOutletName', None)
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
                self._get_oid_for_sensor('ctrlOutletDeciAmps'),
                serial, 'ctrlOutletDeciAmps', u_o_m=Sensor.UNIT_AMPERES,
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
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletPOAAction'),
                serial, 'ctrlOutletPOAAction', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletPOADelay'),
                serial, 'ctrlOutletPOADelay', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletKWattHrs'),
                serial, 'ctrlOutletKWattHrs', name=name))
            sensors.append(self._make_result_dict(
                ctrl_outlet_oid,
                self._get_oid_for_sensor('ctrlOutletPower'),
                serial, 'ctrlOutletPower', name=name))
        return sensors

    @for_table('dewPointSensorTable')
    def _get_dewpoint_sensors_params(self, dewpoint_sensors):
        sensors = []
        for dewpoint_sensor in itervalues(dewpoint_sensors):
            dewpoint_sensor_avail = dewpoint_sensor.get('dewPointSensorAvail',
                                                        None)
            if dewpoint_sensor_avail:
                dewpoint_sensor_oid = dewpoint_sensor.get(0, None)
                serial = dewpoint_sensor.get('dewPointSensorSerial', None)
                name = dewpoint_sensor.get('dewPointSensorName', None)
                sensors.append(self._make_result_dict(
                    dewpoint_sensor_oid,
                    self._get_oid_for_sensor('dewPointSensorTempC'),
                    serial, 'dewPointSensorTempC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
                sensors.append(self._make_result_dict(
                    dewpoint_sensor_oid,
                    self._get_oid_for_sensor('dewPointSensorHumidity'),
                    serial, 'dewPointSensorHumidity',
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY, name=name))
                sensors.append(self._make_result_dict(
                    dewpoint_sensor_oid,
                    self._get_oid_for_sensor('dewPointSensorDewPointC'),
                    serial, 'dewPointSensorDewPointC',
                    u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
        return sensors

    @for_table('digitalSensorTable')
    def _get_digital_sensors_params(self, digital_sensors):
        sensors = []
        for digital_sensor in itervalues(digital_sensors):
            digital_avail = digital_sensor.get('digitalSensorAvail', None)
            if digital_avail:
                digital_sensor_oid = digital_sensor.get(0, None)
                serial = digital_sensor.get('digitalSensorSerial', None)
                name = digital_sensor.get('digitalSensorName', None)
                sensors.append(self._make_result_dict(
                    digital_sensor_oid,
                    self._get_oid_for_sensor('digitalSensorDigital'),
                    serial, 'digitalSensorDigital', name=name))
        return sensors

    @for_table('dstsTable')
    def _get_dsts_params(self, dsts_sensors):
        sensors = []
        for dsts_sensor in itervalues(dsts_sensors):
            dsts_sensor_avail = dsts_sensor.get('dstsAvail', None)
            if dsts_sensor_avail:
                dsts_sensor_oid = dsts_sensor.get(0, None)
                serial = dsts_sensor.get('dstsSerial', None)
                name = dsts_sensor.get('dstsName', None)
                postfixes = [chr(i) for i in range(ord('A'), ord('C'))]
                for pfix in postfixes:
                    sensors.append(self._make_result_dict(
                        dsts_sensor_oid,
                        self._get_oid_for_sensor('dstsVolts' + pfix),
                        serial, 'dstsVolts' + pfix, u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        dsts_sensor_oid,
                        self._get_oid_for_sensor('dstsDeciAmps' + pfix),
                        serial, 'dstsDeciAmps' + pfix,
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

    @for_table('cpmSensorTable')
    def _get_cpm_params(self, cpm_sensors):
        sensors = []
        for cpm_sensor in itervalues(cpm_sensors):
            cpm_sensor_avail = cpm_sensor.get('cpmSensorAvail', None)
            if cpm_sensor_avail:
                cpm_sensor_oid = cpm_sensor.get(0, None)
                serial = cpm_sensor.get('cpmSensorSerial', None)
                name = cpm_sensor.get('cpmSensorName', None)
                sensors.append(self._make_result_dict(
                    cpm_sensor_oid,
                    self._get_oid_for_sensor('cpmSensorStatus'),
                    serial, 'cpmSensorStatus', name=name))
        return sensors

    @for_table('smokeAlarmTable')
    def _get_smoke_alarms_params(self, smoke_alarms):
        sensors = []
        for smoke_alarm in itervalues(smoke_alarms):
            smoke_alarm_avail = smoke_alarm.get('smokeAlarmAvail', None)
            if smoke_alarm_avail:
                smoke_alarm_oid = smoke_alarm.get(0, None)
                serial = smoke_alarm.get('smokeAlarmSerial', None)
                name = smoke_alarm.get('smokeAlarmName', None)
                sensors.append(self._make_result_dict(
                    smoke_alarm_oid,
                    self._get_oid_for_sensor('smokeAlarmStatus'),
                    serial, 'smokeAlarmStatus', name=name))
        return sensors

    @for_table('neg48VdcSensorTable')
    def _get_neg48vdc_sensors_params(self, neg48vdc_sensors):
        sensors = []
        for neg48vdc_sensor in itervalues(neg48vdc_sensors):
            neg48vdc_sensor_avail = neg48vdc_sensor.get('neg48VdcSensorAvail',
                                                        None)
            if neg48vdc_sensor_avail:
                neg48vdc_sensor_oid = neg48vdc_sensor.get(0, None)
                serial = neg48vdc_sensor.get('neg48VdcSensorSerial', None)
                name = neg48vdc_sensor.get('neg48VdcSensorName', None)
                sensors.append(self._make_result_dict(
                    neg48vdc_sensor_oid,
                    self._get_oid_for_sensor('neg48VdcSensorVoltage'),
                    serial, 'neg48VdcSensorVoltage', u_o_m=Sensor.UNIT_VOLTS_DC,
                    name=name))
        return sensors

    @for_table('pos30VdcSensorTable')
    def _get_pos30vdc_sensors_params(self, pos30vdc_sensors):
        sensors = []
        for pos30vdc_sensor in itervalues(pos30vdc_sensors):
            pos30vdc_sensor_avail = pos30vdc_sensor.get('pos30VdcSensorAvail',
                                                        None)
            if pos30vdc_sensor_avail:
                pos30vdc_sensor_oid = pos30vdc_sensor.get(0, None)
                serial = pos30vdc_sensor.get('pos30VdcSensorSerial', None)
                name = pos30vdc_sensor.get('pos30VdcSensorName', None)
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
            analog_avail = analog_sensor.get('analogSensorAvail', None)
            if analog_avail:
                analog_sensor_oid = analog_sensor.get(0, None)
                serial = analog_sensor.get('analogSensorSerial', None)
                name = analog_sensor.get('analogSensorName', None)
                sensors.append(self._make_result_dict(
                    analog_sensor_oid,
                    self._get_oid_for_sensor('analogSensorAnalog'),
                    serial, 'analogSensorAnalog', name=name))
        return sensors

    @for_table('ctrl3ChIECTable')
    def _get_ctrl3_chiects_params(self, ctrl3_chiects):
        sensors = []
        for ctrl3_chiect in itervalues(ctrl3_chiects):
            ctrl3_chiect_avail = ctrl3_chiect.get('ctrl3ChIECAvail', None)
            if ctrl3_chiect_avail:
                ctrl3_chiect_oid = ctrl3_chiect.get(0, None)
                serial = ctrl3_chiect.get('ctrl3ChIECSerial', None)
                name = ctrl3_chiect.get('ctrl3ChIECName', None)
                postfixes = [chr(i) for i in range(ord('A'), ord('D'))]
                for pfix in postfixes:
                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECKWattHrs' + pfix),
                        serial, 'ctrl3ChIECKWattHrs' + pfix, name=name))

                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECVolts' + pfix),
                        serial, 'ctrl3ChIECVolts' + pfix,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECVoltPeak' + pfix),
                        serial, 'ctrl3ChIECVoltPeak' + pfix,
                        u_o_m=Sensor.UNIT_VOLTS_DC,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECDeciAmps' + pfix),
                        serial, 'ctrl3ChIECDeciAmps' + pfix,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECDeciAmpsPeak' +
                                                 pfix),
                        serial, 'ctrl3ChIECDeciAmpsPeak' + pfix,
                        u_o_m=Sensor.UNIT_AMPERES, name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECRealPower' + pfix),
                        serial, 'ctrl3ChIECRealPower' + pfix, name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECApparentPower' +
                                                 pfix),
                        serial, 'ctrl3ChIECApparentPower' + pfix, name=name))
                    sensors.append(self._make_result_dict(
                        ctrl3_chiect_oid,
                        self._get_oid_for_sensor('ctrl3ChIECPowerFactor' +
                                                 pfix),
                        serial, 'ctrl3ChIECPowerFactor' + pfix, name=name))
        return sensors

    @for_table('climateRelayTable')
    def _get_climate_relays_params(self, climate_relays):
        sensors = []
        for climate_relay in itervalues(climate_relays):
            climate_relay_avail = climate_relay.get('climateRelayAvail', None)
            if climate_relay_avail:
                climate_relay_oid = climate_relay.get(0, None)
                serial = climate_relay.get('climateRelaySerial', None)
                name = climate_relay.get('climateRelayName', None)
                sensors.append(self._make_result_dict(
                    climate_relay_oid,
                    self._get_oid_for_sensor('climateRelayTempC'),
                    serial, 'climateRelayTempC', u_o_m=Sensor.UNIT_CELSIUS,
                    name=name))
                for i in range(1, 7):
                    sensors.append(self._make_result_dict(
                        climate_relay_oid,
                        self._get_oid_for_sensor('climateRelayIO' + str(i)),
                        serial, 'climateRelayIO' + str(i), name=name))
        return sensors

    @for_table('ctrlRelayTable')
    def _get_ctrl_relays_params(self, ctrl_relays):
        sensors = []
        for ctrl_relay in itervalues(ctrl_relays):
            ctrl_relay_oid = ctrl_relay.get(0, None)
            serial = ctrl_relay.get('ctrlRelayIndex', None)
            name = ctrl_relay.get('ctrlRelayName', None)
            sensors.append(self._make_result_dict(
                ctrl_relay_oid,
                self._get_oid_for_sensor('ctrlRelayState'),
                serial, 'ctrlRelayState', name=name))
            sensors.append(self._make_result_dict(
                ctrl_relay_oid,
                self._get_oid_for_sensor('ctrlRelayLatchingMode'),
                serial, 'ctrlRelayLatchingMode', name=name))
            sensors.append(self._make_result_dict(
                ctrl_relay_oid,
                self._get_oid_for_sensor('ctrlRelayOverride'),
                serial, 'ctrlRelayOverride', name=name))
            sensors.append(self._make_result_dict(
                ctrl_relay_oid,
                self._get_oid_for_sensor('ctrlRelayAcknowledge'),
                serial, 'ctrlRelayAcknowledge', name=name))
        return sensors

    @for_table('airSpeedSwitchSensorTable')
    def _get_airspeed_switch_sensors_params(self, airspeed_switch_sensors):
        sensors = []
        for airspeed_sensor in itervalues(airspeed_switch_sensors):
            airspeed_avail = airspeed_sensor.get('airSpeedSwitchSensorAvail',
                                                 None)
            if airspeed_avail:
                airspeed_oid = airspeed_sensor.get(0, None)
                serial = airspeed_sensor.get('airSpeedSwitchSensorSerial',
                                             None)
                name = airspeed_sensor.get('airSpeedSwitchSensorName', None)
                sensors.append(self._make_result_dict(
                    airspeed_oid,
                    self._get_oid_for_sensor('airSpeedSwitchSensorAirSpeed'),
                    serial, 'airSpeedSwitchSensorAirSpeed', name=name))
        return sensors

    @for_table('powerDMTable')
    def _get_power_dms_params(self, power_dms):
        sensors = []
        for power_dm in itervalues(power_dms):
            power_dm_avail = power_dm.get('powerDMAvail', None)
            if power_dm_avail:
                power_dm_oid = power_dm.get(0, None)
                serial = power_dm.get('powerDMSerial', None)
                name = power_dm.get('powerDMName', None)
                aux_count = power_dm.get('powerDMUnitInfoAuxCount', None)
                for i in range(1, (aux_count + 1)):
                    aux_numb = str(i)
                    aux_name = (name + ' ' +
                          power_dm.get('powerDMChannelGroup' + aux_numb, None))
                    aux_name += ': ' + power_dm_oid.get('powerDMChannelName' +
                                                        aux_numb, None)
                    aux_name += (' - ' +
                                 power_dm_oid.get('powerDMChannelFriendly' +
                                                  aux_numb, None))
                    sensors.append(self._make_result_dict(
                        power_dm_oid,
                        self._get_oid_for_sensor('powerDMDeciAmps' + aux_numb),
                        serial, 'powerDMDeciAmps' + aux_numb,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=aux_name))
        return sensors

    @for_table('ioExpanderTable')
    def _get_io_expanders_params(self, io_expanders):
        sensors = []
        for io_expander in itervalues(io_expanders):
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
                    sensors.append(self._make_result_dict(
                        io_expander_oid,
                        self._get_oid_for_sensor('ioExpanderIO' + exp_numb),
                        serial, 'ioExpanderIO' + exp_numb, name=exp_name))
                for i in range(1, 4):
                    relay_numb = str(i)
                    relay_name = (name + ': ' +
                                  io_expander.get('ioExpanderRelayName' +
                                                  relay_numb, None))
                    sensors.append(self._make_result_dict(
                        io_expander_oid,
                        self._get_oid_for_sensor('ioExpanderRelayState' +
                                                 relay_numb),
                        serial, 'ioExpanderRelayState' + relay_numb,
                        name=relay_name))
                    sensors.append(self._make_result_dict(
                        io_expander_oid,
                        self._get_oid_for_sensor('ioExpanderRelayLatchingMode' +
                                                 relay_numb),
                        serial, 'ioExpanderRelayLatchingMode' + relay_numb,
                        name=relay_name))
                    sensors.append(self._make_result_dict(
                        io_expander_oid,
                        self._get_oid_for_sensor('ioExpanderRelayOverride' +
                                                 relay_numb),
                        serial, 'ioExpanderRelayOverride' + relay_numb,
                        name=relay_name))
                    sensors.append(self._make_result_dict(
                        io_expander_oid,
                        self._get_oid_for_sensor('ioExpanderRelayAcknowledge' +
                                                 relay_numb),
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
        self._debug('_get_sensor_count: result = %s', result)
        defer.returnValue(result)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """ Try to retrieve all available sensors in this WxGoose"""
        sensor_counts = yield self._get_sensor_count()
        self._debug('get_all_sensors: ip = %s', self.agent_proxy.ip)

        tables = ((self.translate_counter_to_table(counter), count)
                  for counter, count in sensor_counts.items())
        tables = (table for table, count in tables
                  if table and count)

        result = []
        for table in tables:
            self._debug('get_all_sensors: table = %s', table)
            sensors = yield self.retrieve_table(
                                        table).addCallback(reduce_index)
            self._debug('get_all_sensors: %s = %s', table, sensors)
            handler = for_table.map.get(table, None)
            if not handler:
                self._error("There is not data handler for %s", table)
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

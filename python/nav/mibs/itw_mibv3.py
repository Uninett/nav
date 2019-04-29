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
from nav.models.manage import Sensor

from .itw_mib import BaseITWatchDogsMib


TABLES = {
    'climateTable': [
        {
            'avail': 'climateAvail',
            'serial': 'climateSerial',
            'name': 'climateName',
            'sensors': {
                'climateTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'climateHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'climateAirflow': {},
                'climateLight': {},
                'climateSound': {},
                'climateIO1': {},
                'climateIO2': {},
                'climateIO3': {},
                'climateDewPointC': dict(u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'tempSensorTable': [
        {
            'avail': 'tempSensorAvail',
            'serial': 'tempSensorSerial',
            'name': 'tempSensorName',
            'sensors': {
                'tempSensorTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'airFlowSensorTable': [
        {
            'avail': 'airFlowSensorAvail',
            'serial': 'airFlowSensorSerial',
            'name': 'airFlowSensorName',
            'sensors': {
                'airFlowSensorTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'airFlowSensorFlow': {},
                'airFlowSensorHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
                'airFlowSensorDewPointC': dict(u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'doorSensorTable': [
        {
            'avail': 'doorSensorAvail',
            'serial': 'doorSensorSerial',
            'name': 'doorSensorName',
            'sensors': {
                'doorSensorStatus': {},
            }
        }
    ],
    'waterSensorTable': [
        {
            'avail': 'waterSensorAvail',
            'serial': 'waterSensorSerial',
            'name': 'waterSensorName',
            'sensors': {
                'waterSensorDampness': {},
            }
        }
    ],
    'currentMonitorTable': [
        {
            'avail': 'currentMonitorAvail',
            'serial': 'currentMonitorSerial',
            'name': 'currentMonitorName',
            'sensors': {
                'currentMonitorDeciAmps': dict(
                    u_o_m=Sensor.UNIT_AMPERES),
            }
        }
    ],
    'millivoltMonitorTable': [
        {
            'avail': 'millivoltMonitorAvail',
            'serial': 'millivoltMonitorSerial',
            'name': 'millivoltMonitorName',
            'sensors': {
                'millivoltMonitorMV': dict(
                    u_o_m=Sensor.UNIT_VOLTS_DC, scale='milli'),
            }
        }
    ],
    'dewPointSensorTable': [
        {
            'avail': 'dewPointSensorAvail',
            'serial': 'dewPointSensorSerial',
            'name': 'dewPointSensorName',
            'sensors': {
                'dewPointSensorDewPointC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'dewPointSensorTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'dewPointSensorHumidity': dict(
                    u_o_m=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY),
            }
        }
    ],
    'digitalSensorTable': [
        {
            'avail': 'digitalSensorAvail',
            'serial': 'digitalSensorSerial',
            'name': 'digitalSensorName',
            'sensors': {
                'digitalSensorDigital': {},
            }
        }
    ],
    'cpmSensorTable': [
        {
            'avail': 'cpmSensorAvail',
            'serial': 'cpmSensorSerial',
            'name': 'cpmSensorName',
            'sensors': {
                'cpmSensorStatus': {},
            }
        }
    ],
    'smokeAlarmTable': [
        {
            'avail': 'smokeAlarmAvail',
            'serial': 'smokeAlarmSerial',
            'name': 'smokeAlarmName',
            'sensors': {
                'smokeAlarmStatus': {},
            }
        }
    ],
    'neg48VdcSensorTable': [
        {
            'avail': 'neg48VdcSensorAvail',
            'serial': 'neg48VdcSensorSerial',
            'name': 'neg48VdcSensorName',
            'sensors': {
                'neg48VdcSensorVoltage': dict(u_o_m=Sensor.UNIT_VOLTS_DC),
            }
        }
    ],
    'pos30VdcSensorTable': [
        {
            'avail': 'pos30VdcSensorAvail',
            'serial': 'pos30VdcSensorSerial',
            'name': 'pos30VdcSensorName',
            'sensors': {
                'pos30VdcSensorVoltage': dict(u_o_m=Sensor.UNIT_VOLTS_DC),
            }
        }
    ],
    'analogSensorTable': [
        {
            'avail': 'analogSensorAvail',
            'serial': 'analogSensorSerial',
            'name': 'analogSensorName',
            'sensors': {
                'analogSensorAnalog': {},
            }
        }
    ],
    'powMonTable': [
        {
            'avail': 'powMonAvail',
            'serial': 'powMonSerial',
            'name': 'powMonName',
            'sensors': {
                'powMonkWattHrs': dict(u_o_m=Sensor.UNIT_WATTHOURS),
                'powMonVolts': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonVoltMax': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonVoltMin': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonVoltPeak': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'powMonDeciAmps': dict(u_o_m=Sensor.UNIT_AMPERES),
                'powMonRealPower': {},
                'powMonApparentPower': {},
                'powMonPowerFactor': {},
                'powMonOutlet1': {},
                'powMonOutlet2': {},
            }
        }
    ],
    # 'powerTable': [
    #     {
    #         'avail': 'powerAvail',
    #         'serial': 'powerSerial',
    #         'name': 'powerName',
    #         'sensors': {
    #             'powerVolts': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
    #             'powerDeciAmps': dict(u_o_m=Sensor.UNIT_AMPERES),
    #             'powerRealPower': {},
    #             'powerApparentPower': {},
    #             'powerPowerFactor': {},
    #         }
    #     }
    # ],
    'pow3ChTable': [
        {
            'avail': 'pow3ChAvail',
            'serial': 'pow3ChSerial',
            'name': 'pow3ChName',
            'sensors': {
                'pow3ChkWattHrs' + ch: dict(u_o_m=Sensor.UNIT_WATTHOURS),
                'pow3ChVolts' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltMax' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltMin' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltMin' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChVoltPeak' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'pow3ChDeciAmps' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'pow3ChRealPower' + ch: {},
                'pow3ChApparentPower' + ch: {},
                'pow3ChPowerFactor' + ch: {},
            }
        }
        for ch in ('A', 'B', 'C')
    ],
    'outletTable': [
        {
            'avail': 'outletAvail',
            'serial': 'outletSerial',
            'name': 'outletName',
            'sensors': {
                'outlet1Status': {},
                'outlet2Status': {},
            }
        }
    ],
    'vsfcTable': [
        {
            'avail': 'vsfcAvail',
            'serial': 'vsfcSerial',
            'name': 'vsfcName',
            'sensors': {
                'vsfcSetPointC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcFanSpeed': dict(u_o_m=Sensor.UNIT_RPM),
                'vsfcIntTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt1TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt2TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt3TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'vsfcExt4TempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
            }
        }
    ],
    'ctrl3ChTable': [
        {
            'avail': 'ctrl3ChAvail',
            'serial': 'ctrl3ChSerial',
            'name': 'ctrl3ChName',
            'sensors': {
                'ctrl3ChVolts' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'ctrl3ChVoltPeak' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'ctrl3ChDeciAmps' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrl3ChDeciAmpsPeak' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrl3ChRealPower' + ch: dict(u_o_m=Sensor.UNIT_WATTS),
                'ctrl3ChApparentPower' + ch: dict(u_o_m=Sensor.UNIT_VOLTAMPERES),
                'ctrl3ChPowerFactor' + ch: {},
            }
        }
        for ch in ('A', 'B', 'C')
    ],
    'ctrlGrpAmpsTable': [
        {
            'avail': 'ctrlGrpAmpsAvail',
            'serial': 'ctrlGrpAmpsSerial',
            'name': 'ctrlGrpAmpsName',
            'sensors': {
                'ctrlGrpAmps' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrlGrpAmps' + ch + 'Volts': dict(u_o_m=Sensor.UNIT_VOLTS_AC),
            }
        }
        for ch in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
    ],
    'ctrlOutletTable': [
        {
            'avail': 'ctrlOutletName',  # this table has no Avail column.
            'serial': 'ctrlOutletIndex',  # and serial
            'name': 'ctrlOutletName',  # FIXME name does not match previous implementation
            'sensors': {
                'ctrlOutletStatus': {},
                'ctrlOutletFeedback': {},
                'ctrlOutletPending': {},
                'ctrlOutletDeciAmps': dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrlOutletUpDelay': {},
                'ctrlOutletDwnDelay': {},
                'ctrlOutletRbtDelay': {},
                'ctrlOutletPOAAction': {},
                'ctrlOutletPOADelay': {},
                'ctrlOutletkWattHrs': {},
                'ctrlOutletPower': {},
            }
        }
    ],
    'dstsTable': [
        {
            'avail': 'dstsAvail',
            'serial': 'dstsSerial',
            'name': 'dstsName',
            'sensors': {
                'dstsVolts' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_DC),
                'dstsDeciAmps' + ch: dict(
                        u_o_m=Sensor.UNIT_AMPERES),
                'dstsSource' + ch + 'Active': {},
                'dstsPowerStatus' + ch: {},
                'dstsSource' + ch + 'TempC': {},
            }
        }
        for ch in ('A', 'B')
    ],
    'ctrlRelayTable': [
        {
            'avail': 'ctrlRelayName',  # No avail
            'serial': 'ctrlRelayIndex',
            'name': 'ctrlRelayName',
            'sensors': {
                'ctrlRelayState': {},
                'ctrlRelayLatchingMode': {},
                'ctrlRelayOverride': {},
                'ctrlRelayAcknowledge': {},
            }
        }
    ],
    'climateRelayTable': [
        {
            'avail': 'climateRelayAvail',
            'serial': 'climateRelaySerial',
            'name': 'climateRelayName',
            'sensors': {
                'climateRelayTempC': dict(u_o_m=Sensor.UNIT_CELSIUS),
                'climateRelayIO1': {},
                'climateRelayIO2': {},
                'climateRelayIO3': {},
                'climateRelayIO4': {},
                'climateRelayIO5': {},
                'climateRelayIO6': {},
            }
        }
    ],
    'airSpeedSwitchSensorTable': [
        {
            'avail': 'airSpeedSwitchSensorAvail',
            'serial': 'airSpeedSwitchSensorSerial',
            'name': 'airSpeedSwitchSensorName',
            'sensors': {
                'airSpeedSwitchSensorAirSpeed': {},
            }
        }
    ],
    'ctrl3ChIECTable': [
        {
            'avail': 'ctrl3ChIECAvail',
            'serial': 'ctrl3ChIECSerial',
            'name': 'ctrl3ChIECName',
            'sensors': {
                'ctrl3ChIECkWattHrs' + ch: {},
                'ctrl3ChIECVolts' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'ctrl3ChIECVoltPeak' + ch: dict(u_o_m=Sensor.UNIT_VOLTS_AC),
                'ctrl3ChIECDeciAmps' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrl3ChIECDeciAmpsPeak' + ch: dict(u_o_m=Sensor.UNIT_AMPERES),
                'ctrl3ChIECRealPower' + ch: dict(u_o_m=Sensor.UNIT_WATTS),
                'ctrl3ChIECApparentPower' + ch: dict(u_o_m=Sensor.UNIT_VOLTAMPERES),
                'ctrl3ChIECPowerFactor' + ch: {},
            }
        }
        for ch in ('A', 'B', 'C')
    ]
}


class ItWatchDogsMibV3(BaseITWatchDogsMib):
    """A class that tries to retrieve all sensors from WeatherGoose II"""
    mib = get_mib('IT-WATCHDOGS-MIB-V3')
    TABLES = TABLES

    def _debug(self, msg, *args, **kwargs):
        return self._logger.debug(self.__class__.__name__ + ":: " + msg,
                                  *args, **kwargs)

    def _error(self, msg, *args, **kwargs):
        return self._logger.error(self.__class__.__name__ + ":: " + msg,
                                  *args, **kwargs)

    def _get_power_dms_params(self, power_dms):
        sensors = []
        for power_dm in itervalues(power_dms):
            power_dm_avail = power_dm.get('powerDMAvail')
            if power_dm_avail:
                power_dm_oid = power_dm.get(0)
                serial = power_dm.get('powerDMSerial')
                name = power_dm.get('powerDMName')
                aux_count = power_dm.get('powerDMUnitInfoAuxCount')
                for i in range(1, (aux_count + 1)):
                    aux_numb = str(i)
                    aux_name = (name + ' ' +
                          power_dm.get('powerDMChannelGroup' + aux_numb))
                    aux_name += ': ' + power_dm_oid.get('powerDMChannelName' +
                                                        aux_numb)
                    aux_name += (' - ' +
                                 power_dm_oid.get('powerDMChannelFriendly' +
                                                  aux_numb))
                    sensors.append(self._make_result_dict(
                        power_dm_oid,
                        self._get_oid_for_sensor('powerDMDeciAmps' + aux_numb),
                        serial, 'powerDMDeciAmps' + aux_numb,
                        u_o_m=Sensor.UNIT_AMPERES,
                        name=aux_name))
        return sensors

    def _get_io_expanders_params(self, io_expanders):
        sensors = []
        for io_expander in itervalues(io_expanders):
            io_expander_avail = io_expander.get('ioExpanderAvail', 0)
            if io_expander_avail:
                io_expander_oid = io_expander.get(0)
                serial = io_expander.get('ioExpanderSerial')
                name = io_expander.get('ioExpanderName')
                for i in range(1, 33):
                    exp_numb = str(i)
                    exp_name = (name + ': ' +
                                io_expander.get('ioExpanderFriendlyName' +
                                                exp_numb))
                    sensors.append(self._make_result_dict(
                        io_expander_oid,
                        self._get_oid_for_sensor('ioExpanderIO' + exp_numb),
                        serial, 'ioExpanderIO' + exp_numb, name=exp_name))
                for i in range(1, 4):
                    relay_numb = str(i)
                    relay_name = (name + ': ' +
                                  io_expander.get('ioExpanderRelayName' +
                                                  relay_numb))
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
    def get_all_sensors(self):
        """ Try to retrieve all available sensors in this WxGoose"""
        result = yield super(ItWatchDogsMibV3, self).get_all_sensors()

        custom_tables = {
            'powerDMTable': self._get_power_dms_params,
            'ioExpanderTable': self._get_io_expanders_params,
        }
        for table, handler in custom_tables.items():
            self._debug('get_all_sensors: table = %s', table)
            sensors = yield self.retrieve_table(
                                        table).addCallback(reduce_index)
            self._debug('get_all_sensors: %s = %s', table, sensors)
            result.extend(handler(sensors))

        defer.returnValue(result)

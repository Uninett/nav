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

    def retrieve_std_columns(self):
        """ A convenient function for getting the most interesting
        columns for environment mibs. """

        return self.retrieve_columns([
                'pow3ChSerial',
                'pow3ChName',
                'pow3ChAvail',
                'pow3ChKWattHrsA',
                'pow3ChVoltsA',
                'pow3ChDeciAmpsA'
                'pow3ChVoltMaxA',
                'pow3ChVoltMinA',
                'pow3ChVoltPeakA',
                'pow3ChDeciAmpsA',
                'pow3ChRealPowerA',
                'pow3ChApparentPowerA',
                'pow3ChPowerFactorA',
                'pow3ChKWattHrsB',
                'pow3ChVoltsB',
                'pow3ChVoltMaxB',
                'pow3ChVoltMinB',
                'pow3ChVoltPeakB',
                'pow3ChDeciAmpsB',
                'pow3ChRealPowerB',
                'pow3ChApparentPowerB',
                'pow3ChPowerFactorB',
                'pow3ChKWattHrsC',
                'pow3ChVoltsC',
                'pow3ChVoltMaxC',
                'pow3ChVoltMinC',
                'pow3ChVoltPeakC',
                'pow3ChDeciAmpsC',
                'pow3ChRealPowerC',
                'pow3ChApparentPowerC',
                'pow3ChPowerFactorC',
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
                'vsfcFanSpeed',
                'vsfcIntTempC',
                'vsfcExt1TempC',
                'vsfcExt2TempC',
                'vsfcExt3TempC',
                'vsfcExt4TempC',
                #
                'ctrl3ChSerial',
                'ctrl3ChName',
                'ctrl3ChAvail',
                'ctrl3ChVoltsA',
                'ctrl3ChVoltPeakA',
                'ctrl3ChDeciAmpsA',
                'ctrl3ChDeciAmpsPeakA',
                'ctrl3ChRealPowerA',
                'ctrl3ChApparentPowerA',
                'ctrl3ChPowerFactorA',
                'ctrl3ChVoltsB',
                'ctrl3ChVoltPeakB',
                'ctrl3ChDeciAmpsB',
                'ctrl3ChDeciAmpsPeakB',
                'ctrl3ChRealPowerB',
                'ctrl3ChApparentPowerB',
                'ctrl3ChPowerFactorB',
                'ctrl3ChVoltsC',
                'ctrl3ChVoltPeakC',
                'ctrl3ChDeciAmpsC',
                'ctrl3ChDeciAmpsPeakC',
                'ctrl3ChRealPowerC',
                'ctrl3ChApparentPowerC',
                'ctrl3ChPowerFactorC',
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
                'ctrlGrpAmpsG',
                'ctrlGrpAmpsH',
                'ctrlGrpAmpsAVolts',
                'ctrlGrpAmpsBVolts',
                'ctrlGrpAmpsCVolts',
                'ctrlGrpAmpsDVolts',
                'ctrlGrpAmpsEVolts',
                'ctrlGrpAmpsFVolts',
                'ctrlGrpAmpsGVolts',
                'ctrlGrpAmpsHVolts',
                #
                'ctrlOutletName',
                'ctrlOutletStatus',
                'ctrlOutletFeedback',
                'ctrlOutletPending',
                'ctrlOutletDeciAmps',
                'ctrlOutletGroup',
                'ctrlOutletUpDelay',
                'ctrlOutletDwnDelay',
                'ctrlOutletRbtDelay',
                'ctrlOutletURL',
                'ctrlOutletPOAAction',
                'ctrlOutletPOADelay',
                'ctrlOutletKWattHrs',
                'ctrlOutletPower',
                #
                'dewPointSensorSerial',
                'dewPointSensorName',
                'dewPointSensorAvail',
                'dewPointSensorTempC',
                'dewPointSensorHumidity',
                'dewPointSensorDewPointC',
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
                'dstsDeciAmpsA',
                'dstsVoltsB',
                'dstsDeciAmpsB',
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
                #
                'ctrl3ChIECSerial',
                'ctrl3ChIECName',
                'ctrl3ChIECAvail',
                'ctrl3ChIECKWattHrsA',
                'ctrl3ChIECVoltsA',
                'ctrl3ChIECVoltPeakA',
                'ctrl3ChIECDeciAmpsA',
                'ctrl3ChIECDeciAmpsPeakA',
                'ctrl3ChIECRealPowerA',
                'ctrl3ChIECApparentPowerA',
                'ctrl3ChIECPowerFactorA',
                'ctrl3ChIECKWattHrsB',
                'ctrl3ChIECVoltsB',
                'ctrl3ChIECVoltPeakB',
                'ctrl3ChIECDeciAmpsB',
                'ctrl3ChIECDeciAmpsPeakB',
                'ctrl3ChIECRealPowerB',
                'ctrl3ChIECApparentPowerB',
                'ctrl3ChIECPowerFactorB',
                'ctrl3ChIECKWattHrsC',
                'ctrl3ChIECVoltsC',
                'ctrl3ChIECVoltPeakC',
                'ctrl3ChIECDeciAmpsC',
                'ctrl3ChIECDeciAmpsPeakC',
                'ctrl3ChIECRealPowerC',
                'ctrl3ChIECApparentPowerC',
                'ctrl3ChIECPowerFactorC',
                #
                'climateRelaySerial',
                'climateRelayName',
                'climateRelayAvail',
                'climateRelayTempC',
                'climateRelayIO1',
                'climateRelayIO2',
                'climateRelayIO3',
                'climateRelayIO4',
                'climateRelayIO5',
                'climateRelayIO6',
                #
                'ctrlRelayName',
                'ctrlRelayState',
                'ctrlRelayLatchingMode',
                'ctrlRelayOverride',
                'ctrlRelayAcknowledge',
                #
                'airSpeedSwitchSensorSerial',
                'airSpeedSwitchSensorName',
                'airSpeedSwitchSensorAvail',
                'airSpeedSwitchSensorAirSpeed',
                #
                'powerDMSerial',
                'powerDMName',
                'powerDMAvail',
                'powerDMUnitInfoTitle',
                'powerDMUnitInfoVersion',
                'powerDMUnitInfoMainCount',
                'powerDMUnitInfoAuxCount',
                'powerDMChannelName1',
                'powerDMChannelName2',
                'powerDMChannelName3',
                'powerDMChannelName4',
                'powerDMChannelName5',
                'powerDMChannelName6',
                'powerDMChannelName7',
                'powerDMChannelName8',
                'powerDMChannelName9',
                'powerDMChannelName10',
                'powerDMChannelName11',
                'powerDMChannelName12',
                'powerDMChannelName13',
                'powerDMChannelName14',
                'powerDMChannelName15',
                'powerDMChannelName16',
                'powerDMChannelName17',
                'powerDMChannelName18',
                'powerDMChannelName19',
                'powerDMChannelName20',
                'powerDMChannelName21',
                'powerDMChannelName22',
                'powerDMChannelName23',
                'powerDMChannelName24',
                'powerDMChannelName25',
                'powerDMChannelName26',
                'powerDMChannelName27',
                'powerDMChannelName28',
                'powerDMChannelName29',
                'powerDMChannelName30',
                'powerDMChannelName31',
                'powerDMChannelName32',
                'powerDMChannelName33',
                'powerDMChannelName34',
                'powerDMChannelName35',
                'powerDMChannelName36',
                'powerDMChannelName37',
                'powerDMChannelName38',
                'powerDMChannelName39',
                'powerDMChannelName40',
                'powerDMChannelName41',
                'powerDMChannelName42',
                'powerDMChannelName43',
                'powerDMChannelName44',
                'powerDMChannelName45',
                'powerDMChannelName46',
                'powerDMChannelName47',
                'powerDMChannelName48',
                'powerDMChannelFriendly1',
                'powerDMChannelFriendly2',
                'powerDMChannelFriendly3',
                'powerDMChannelFriendly4',
                'powerDMChannelFriendly5',
                'powerDMChannelFriendly6',
                'powerDMChannelFriendly7',
                'powerDMChannelFriendly8',
                'powerDMChannelFriendly9',
                'powerDMChannelFriendly10',
                'powerDMChannelFriendly11',
                'powerDMChannelFriendly12',
                'powerDMChannelFriendly13',
                'powerDMChannelFriendly14',
                'powerDMChannelFriendly15',
                'powerDMChannelFriendly16',
                'powerDMChannelFriendly17',
                'powerDMChannelFriendly18',
                'powerDMChannelFriendly19',
                'powerDMChannelFriendly20',
                'powerDMChannelFriendly21',
                'powerDMChannelFriendly22',
                'powerDMChannelFriendly23',
                'powerDMChannelFriendly24',
                'powerDMChannelFriendly25',
                'powerDMChannelFriendly26',
                'powerDMChannelFriendly27',
                'powerDMChannelFriendly28',
                'powerDMChannelFriendly29',
                'powerDMChannelFriendly30',
                'powerDMChannelFriendly31',
                'powerDMChannelFriendly32',
                'powerDMChannelFriendly33',
                'powerDMChannelFriendly34',
                'powerDMChannelFriendly35',
                'powerDMChannelFriendly36',
                'powerDMChannelFriendly37',
                'powerDMChannelFriendly38',
                'powerDMChannelFriendly38',
                'powerDMChannelFriendly40',
                'powerDMChannelFriendly41',
                'powerDMChannelFriendly42',
                'powerDMChannelFriendly43',
                'powerDMChannelFriendly44',
                'powerDMChannelFriendly45',
                'powerDMChannelFriendly46',
                'powerDMChannelFriendly47',
                'powerDMChannelFriendly48',
                'powerDMChannelGroup1',
                'powerDMChannelGroup2',
                'powerDMChannelGroup3',
                'powerDMChannelGroup4',
                'powerDMChannelGroup5',
                'powerDMChannelGroup6',
                'powerDMChannelGroup7',
                'powerDMChannelGroup8',
                'powerDMChannelGroup9',
                'powerDMChannelGroup10',
                'powerDMChannelGroup11',
                'powerDMChannelGroup12',
                'powerDMChannelGroup13',
                'powerDMChannelGroup14',
                'powerDMChannelGroup15',
                'powerDMChannelGroup16',
                'powerDMChannelGroup17',
                'powerDMChannelGroup18',
                'powerDMChannelGroup19',
                'powerDMChannelGroup20',
                'powerDMChannelGroup21',
                'powerDMChannelGroup22',
                'powerDMChannelGroup23',
                'powerDMChannelGroup24',
                'powerDMChannelGroup25',
                'powerDMChannelGroup26',
                'powerDMChannelGroup27',
                'powerDMChannelGroup28',
                'powerDMChannelGroup29',
                'powerDMChannelGroup30',
                'powerDMChannelGroup31',
                'powerDMChannelGroup32',
                'powerDMChannelGroup33',
                'powerDMChannelGroup34',
                'powerDMChannelGroup35',
                'powerDMChannelGroup36',
                'powerDMChannelGroup37',
                'powerDMChannelGroup38',
                'powerDMChannelGroup39',
                'powerDMChannelGroup40',
                'powerDMChannelGroup41',
                'powerDMChannelGroup42',
                'powerDMChannelGroup43',
                'powerDMChannelGroup44',
                'powerDMChannelGroup45',
                'powerDMChannelGroup46',
                'powerDMChannelGroup47',
                'powerDMChannelGroup48',
                'powerDMDeciAmps1',
                'powerDMDeciAmps2',
                'powerDMDeciAmps3',
                'powerDMDeciAmps4',
                'powerDMDeciAmps5',
                'powerDMDeciAmps6',
                'powerDMDeciAmps7',
                'powerDMDeciAmps8',
                'powerDMDeciAmps9',
                'powerDMDeciAmps10',
                'powerDMDeciAmps11',
                'powerDMDeciAmps12',
                'powerDMDeciAmps13',
                'powerDMDeciAmps14',
                'powerDMDeciAmps15',
                'powerDMDeciAmps16',
                'powerDMDeciAmps17',
                'powerDMDeciAmps18',
                'powerDMDeciAmps19',
                'powerDMDeciAmps20',
                'powerDMDeciAmps21',
                'powerDMDeciAmps22',
                'powerDMDeciAmps23',
                'powerDMDeciAmps24',
                'powerDMDeciAmps25',
                'powerDMDeciAmps26',
                'powerDMDeciAmps27',
                'powerDMDeciAmps28',
                'powerDMDeciAmps29',
                'powerDMDeciAmps30',
                'powerDMDeciAmps31',
                'powerDMDeciAmps32',
                'powerDMDeciAmps33',
                'powerDMDeciAmps34',
                'powerDMDeciAmps35',
                'powerDMDeciAmps36',
                'powerDMDeciAmps37',
                'powerDMDeciAmps38',
                'powerDMDeciAmps39',
                'powerDMDeciAmps40',
                'powerDMDeciAmps41',
                'powerDMDeciAmps42',
                'powerDMDeciAmps43',
                'powerDMDeciAmps44',
                'powerDMDeciAmps45',
                'powerDMDeciAmps46',
                'powerDMDeciAmps47',
                'powerDMDeciAmps48',
                #
                'ioExpanderSerial',
                'ioExpanderName',
                'ioExpanderAvail',
                'ioExpanderFriendlyName1',
                'ioExpanderFriendlyName2',
                'ioExpanderFriendlyName3',
                'ioExpanderFriendlyName4',
                'ioExpanderFriendlyName5',
                'ioExpanderFriendlyName6',
                'ioExpanderFriendlyName7',
                'ioExpanderFriendlyName8',
                'ioExpanderFriendlyName9',
                'ioExpanderFriendlyName10',
                'ioExpanderFriendlyName11',
                'ioExpanderFriendlyName12',
                'ioExpanderFriendlyName13',
                'ioExpanderFriendlyName14',
                'ioExpanderFriendlyName15',
                'ioExpanderFriendlyName16',
                'ioExpanderFriendlyName17',
                'ioExpanderFriendlyName18',
                'ioExpanderFriendlyName19',
                'ioExpanderFriendlyName20',
                'ioExpanderFriendlyName21',
                'ioExpanderFriendlyName22',
                'ioExpanderFriendlyName23',
                'ioExpanderFriendlyName24',
                'ioExpanderFriendlyName25',
                'ioExpanderFriendlyName26',
                'ioExpanderFriendlyName27',
                'ioExpanderFriendlyName28',
                'ioExpanderFriendlyName29',
                'ioExpanderFriendlyName30',
                'ioExpanderFriendlyName31',
                'ioExpanderFriendlyName32',
                'ioExpanderIO1',
                'ioExpanderIO2',
                'ioExpanderIO3',
                'ioExpanderIO4',
                'ioExpanderIO5',
                'ioExpanderIO6',
                'ioExpanderIO7',
                'ioExpanderIO8',
                'ioExpanderIO9',
                'ioExpanderIO10',
                'ioExpanderIO11',
                'ioExpanderIO12',
                'ioExpanderIO13',
                'ioExpanderIO14',
                'ioExpanderIO15',
                'ioExpanderIO16',
                'ioExpanderIO17',
                'ioExpanderIO18',
                'ioExpanderIO19',
                'ioExpanderIO20',
                'ioExpanderIO21',
                'ioExpanderIO22',
                'ioExpanderIO23',
                'ioExpanderIO24',
                'ioExpanderIO25',
                'ioExpanderIO26',
                'ioExpanderIO27',
                'ioExpanderIO28',
                'ioExpanderIO29',
                'ioExpanderIO30',
                'ioExpanderIO31',
                'ioExpanderIO32',
                'ioExpanderRelayName1',
                'ioExpanderRelayState1',
                'ioExpanderRelayLatchingMode1',
                'ioExpanderRelayOverride1',
                'ioExpanderRelayAcknowledge1',
                'ioExpanderRelayName2',
                'ioExpanderRelayState2',
                'ioExpanderRelayLatchingMode2',
                'ioExpanderRelayOverride2',
                'ioExpanderRelayAcknowledge2',
                'ioExpanderRelayName3',
                'ioExpanderRelayState3',
                'ioExpanderRelayLatchingMode3',
                'ioExpanderRelayOverride3',
                'ioExpanderRelayAcknowledge3',
                ])

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
                                self.nodes.get('airFlowSensorHumidity', None)
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
                                self.nodes.get('currentMonitorDeciAmps', None)
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
        return sensors

    @for_table('outletTable')
    def _get_outlet_params(self, outlets):
        sensors = []
        return sensors

    @for_table('vsfcTable')
    def _get_vsfc_params(self, vsfcs):
        sensors = []
        return sensors

    @for_table('ctrl3ChTable')
    def _get_ctrl3_ch_params(self, ctrl3_chs):
        sensors = []
        return sensors

    @for_table('ctrlGrpAmpsTable')
    def _get_ctrl_grp_amps_params(self, ctrl_grp_amps):
        sensors = []
        return sensors

    @for_table('ctrlOutletTable')
    def _get_ctrl_outlet_params(self, ctrl_outlets):
        sensors = []
        return sensors

    @for_table('dewPointSensorTable')
    def _get_dew_point_sensors_params(self, dew_point_sensors):
        sensors = []
        return sensors

    @for_table('digitalSensorTable')
    def _get_digital_sensors_params(self, digital_sensors):
        sensors = []
        return sensors

    @for_table('dstsTable')
    def _get_dsts_params(self, dsts):
        sensors = []
        return sensors

    @for_table('cpmSensorTable')
    def _get_cpm_params(self, cpms):
        sensors = []
        return sensors

    @for_table('smokeAlarmTable')
    def _get_smoke_alarms_params(self, smoke_alarms):
        sensors = []
        return sensors

    @for_table('neg48VdcSensorTable')
    def _get_neg_48vdc_sensors_params(self, neg_48vdc_sensors):
        sensors = []
        return sensors

    @for_table('pos30VdcSensorTable')
    def _get_pos_30vdc_sensors_params(self, pos_30vdc_sensors):
        sensors = []
        return sensors

    @for_table('analogSensorTable')
    def _get_analog_sensors_params(self, analog_sensors):
        sensors = []
        return sensors

    @for_table('ctrl3ChIECTable')
    def _get_ctrl3_chiects_params(self, ctrl3_chiects):
        sensors = []
        return sensors

    @for_table('climateRelayTable')
    def _get_climate_relays_params(self, climate_relays):
        sensors = []
        return sensors

    @for_table('ctrlRelayTable')
    def _get_ctrl_relays_params(self, ctrl_relays):
        sensors = []
        return sensors

    @for_table('airSpeedSwitchSensorTable')
    def _get_airspeed_switch_sensors_params(self, airspeed_switch_sensors):
        sensors = []
        return sensors

    @for_table('powerDMTable')
    def _get_power_dms_params(self, power_dms):
        sensors = []
        return sensors

    @for_table('ioExpanderTable')
    def _get_io_expanders_params(self, io_expanders):
        sensors = []
        return sensors

    @defer.inlineCallbacks
    def get_all_sensors(self):
        defer.returnValue([])

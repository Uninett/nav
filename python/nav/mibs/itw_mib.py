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
from twisted.internet import threads

from nav.mibs import reduce_index

import mibretriever

class ItWatchDogsMib(mibretriever.MibRetriever):
    from nav.smidumps.itw_mib import MIB as mib

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
    def _get_product_info(self):
        """ Get some basic information about netbox"""
        df = self.retrieve_columns([
                        'deviceInfo',
                        'productTitle',
                        'productVersion',
                        'productFriendlyName',
                        ])
        df.addCallback(reduce_index)
        return df

    @defer.inlineCallbacks
    def can_return_sensors(self):
         """ It seems to me that old and new equipment
            have different oids for this information.
            Therefore we can use this to differentiate
            between mibs to use."""
        product_info = yield self._get_product_info()
        if len(product_info) > 0:
            defer.returnValue(True)
        defer.returnValue(False)

    @defer.inlineCallbacks
    def get_all_sensors(self):
        self.logger.error('ItWatchDogsMib:: get_all_sensors:  TADA!!!!')
        defer.returnValue([])

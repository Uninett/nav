#
# Copyright (C) 2008-2014 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A class for extracting information from APC devices"""
from twisted.internet import defer
from nav.mibs import reduce_index
from nav.mibs.ups_mib import UpsMib

R_PDU_LOAD_STATUS_LOAD = 'rPDULoadStatusLoad'
R_PDU_LOAD_STATUS_BANK_NUMBER = 'rPDULoadStatusBankNumber'

U_VOLT = dict(u_o_m='Volt')
U_DECIVOLT = dict(u_o_m='Volt', precision=1)
U_AMPERE = dict(u_o_m='Ampere')
U_DECIAMPERE = dict(u_o_m='Ampere', precision=1)
U_HZ = dict(u_o_m='Hz')
U_DECIHZ = dict(u_o_m='Hz', precision=1)
U_PERCENT = dict(u_o_m='Percent')
U_DECIPERCENT = dict(u_o_m='Percent', precision=1)
U_CELSIUS = dict(u_o_m='Celsius')
U_DECICELSIUS = dict(u_o_m='Celsius', precision=1)
U_TIMETICKS = dict(u_o_m='Seconds', precision=2)


class PowerNetMib(UpsMib):
    """ Custom class for retrieveing sensors from APC UPSes."""
    from nav.smidumps.powernet_mib import MIB as mib

    sensor_columns = {
        'atsInputVoltage': U_VOLT,

        'mUpsEnvironAmbientTemperature': U_CELSIUS,

        'upsAdvBatteryActualVoltage': U_VOLT,
        'upsAdvBatteryCapacity': U_PERCENT,
        'upsAdvBatteryCurrent': U_AMPERE,
        'upsAdvBatteryNominalVoltage': U_VOLT,
        'upsAdvBatteryNumOfBadBattPacks': dict(u_o_m='batteries'),
        'upsAdvBatteryNumOfBattPacks': dict(u_o_m='batteries'),
        'upsAdvBatteryRunTimeRemaining': U_TIMETICKS,
        'upsAdvBatteryTemperature': U_CELSIUS,

        'upsAdvInputFrequency': U_HZ,
        'upsAdvInputLineVoltage': U_VOLT,
        'upsAdvInputMaxLineVoltage': U_VOLT,
        'upsAdvInputMinLineVoltage': U_VOLT,

        'upsAdvOutputCurrent': U_AMPERE,
        'upsAdvOutputFrequency': U_HZ,
        'upsAdvOutputLoad': U_PERCENT,
        'upsAdvOutputVoltage': U_VOLT,

        'upsAdvTotalDCCurrent': U_AMPERE,

        'upsBasicBatteryTimeOnBattery': U_TIMETICKS,
        'upsBasicOutputPhase': dict(u_o_m='Phase'),

        'upsHighPrecBatteryActualVoltage': U_DECIVOLT,
        'upsHighPrecBatteryCapacity': U_DECIPERCENT,
        'upsHighPrecBatteryTemperature': U_DECICELSIUS,

        'upsHighPrecInputFrequency': U_DECIHZ,
        'upsHighPrecInputLineVoltage': U_DECIVOLT,
        'upsHighPrecInputMaxLineVoltage': U_DECIVOLT,
        'upsHighPrecInputMinLineVoltage': U_DECIVOLT,

        'upsHighPrecOutputCurrent': U_DECIAMPERE,
        'upsHighPrecOutputFrequency': U_DECIHZ,
        'upsHighPrecOutputLoad': U_DECIPERCENT,
        'upsHighPrecOutputVoltage': U_DECIVOLT,
    }

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Gets all the interesting sensors for this device."""
        ups_sensors = yield super(PowerNetMib, self).get_all_sensors()
        pdu_sensors = yield self._get_pdu_bank_load_sensors()
        result = ups_sensors + pdu_sensors
        defer.returnValue(result)

    @defer.inlineCallbacks
    def _get_pdu_bank_load_sensors(self):
        banks = yield self.retrieve_columns([R_PDU_LOAD_STATUS_LOAD,
                                             R_PDU_LOAD_STATUS_BANK_NUMBER])
        banks = reduce_index(banks)
        if banks:
            self._logger.debug("Got pdu load status: %r", banks)

        result = []
        column = self.nodes.get(R_PDU_LOAD_STATUS_LOAD, None)
        for index, row in banks.iteritems():
            oid = str(column.oid + str(index))

            bank_number = row.get(R_PDU_LOAD_STATUS_BANK_NUMBER, None)
            name = "PDU Bank %s" % bank_number

            result.append(dict(
                oid=oid,
                unit_of_measurement='Ampere',
                precision=1,
                scale=None,
                description='%s ampere load' % name,
                name=name,
                internal_name='%s%s' % (R_PDU_LOAD_STATUS_LOAD, index),
                mib=self.get_module_name()
            ))
        defer.returnValue(result)

    @defer.inlineCallbacks
    def get_serial_number(self):
        """Tries to get a serial number from an APC device"""
        candidates = [k for k in self.nodes.keys()
                      if 'IdentSerialNumber' in k]
        for c in candidates:
            serial = yield self.get_next(c)
            if serial:
                defer.returnValue(serial)

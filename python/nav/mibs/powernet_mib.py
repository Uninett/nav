#
# Copyright (C) 2008-2014 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
from nav.smidumps import get_mib
from nav.mibs import reduce_index
from nav.mibs.ups_mib import UpsMib
from nav.models.manage import Sensor

R_PDU_LOAD_STATUS_LOAD = 'rPDULoadStatusLoad'
R_PDU_LOAD_STATUS_BANK_NUMBER = 'rPDULoadStatusBankNumber'
R_PDU_LOAD_STATUS_PHASE_NUMBER = 'rPDULoadStatusPhaseNumber'

U_VOLT = dict(u_o_m=Sensor.UNIT_VOLTS_AC)
U_DECIVOLT = dict(u_o_m=Sensor.UNIT_VOLTS_AC, precision=1)
U_AMPERE = dict(u_o_m=Sensor.UNIT_AMPERES)
U_DECIAMPERE = dict(u_o_m=Sensor.UNIT_AMPERES, precision=1)
U_HZ = dict(u_o_m=Sensor.UNIT_HERTZ)
U_DECIHZ = dict(u_o_m=Sensor.UNIT_HERTZ, precision=1)
U_PERCENT = dict(u_o_m=Sensor.UNIT_PERCENT)
U_DECIPERCENT = dict(u_o_m=Sensor.UNIT_PERCENT, precision=1)
U_CELSIUS = dict(u_o_m=Sensor.UNIT_CELSIUS)
U_DECICELSIUS = dict(u_o_m=Sensor.UNIT_CELSIUS, precision=1)
U_TIMETICKS = dict(u_o_m=Sensor.UNIT_SECONDS, precision=2)


class PowerNetMib(UpsMib):
    """Custom class for retrieveing sensors from APC UPSes."""

    mib = get_mib('PowerNet-MIB')

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
        return result

    @defer.inlineCallbacks
    def _get_pdu_bank_load_sensors(self):
        banks = yield self.retrieve_columns(
            [
                R_PDU_LOAD_STATUS_LOAD,
                R_PDU_LOAD_STATUS_PHASE_NUMBER,
                R_PDU_LOAD_STATUS_BANK_NUMBER,
            ]
        )
        banks = reduce_index(banks)
        if banks:
            self._logger.debug("Got pdu load status: %r", banks)

        result = []
        column = self.nodes.get(R_PDU_LOAD_STATUS_LOAD, None)
        for index, row in banks.items():
            oid = str(column.oid + str(index))

            bank_number = row.get(R_PDU_LOAD_STATUS_BANK_NUMBER, None)
            phase_number = row.get(R_PDU_LOAD_STATUS_PHASE_NUMBER, None)
            if bank_number != 0:
                name = "PDU Bank %s" % bank_number
            else:
                name = "PDU Phase %s" % phase_number

            result.append(
                dict(
                    oid=oid,
                    unit_of_measurement=Sensor.UNIT_AMPERES,
                    precision=1,
                    scale=None,
                    description='%s ampere load' % name,
                    name=name,
                    internal_name='%s%s' % (R_PDU_LOAD_STATUS_LOAD, index),
                    mib=self.get_module_name(),
                )
            )
        return result

    @defer.inlineCallbacks
    def get_serial_number(self):
        """Tries to get a serial number from an APC device"""
        candidates = [k for k in self.nodes.keys() if 'IdentSerialNumber' in k]
        for c in candidates:
            serial = yield self.get_next(c)
            if serial:
                if isinstance(serial, bytes):
                    serial = serial.decode("utf-8")
                return serial

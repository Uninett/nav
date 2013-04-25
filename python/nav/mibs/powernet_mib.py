#
# Copyright (C) 2008-2013 UNINETT AS
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


class PowerNetMib(UpsMib):
    """ Custom class for retrieveing sensors from APC UPSes."""
    from nav.smidumps.powernet_mib import MIB as mib

    sensor_columns = {
        'atsInputVoltage': {
            'u_o_m': 'Volts',
        },
        'upsAdvInputFrequency': {
            'u_o_m': 'Hz',
        },
        'upsAdvOutputCurrent': {
            'u_o_m': 'Amperes',
        },
        'mUpsEnvironAmbientTemperature': {
            'u_o_m': 'Celsius',
        },
        'upsAdvBatteryCapacity': {
            'u_o_m': 'Percent',
        },
        'upsBasicBatteryTimeOnBattery': {
            'u_o_m': 'Seconds',
            'scale': 'centi'
        },
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
                unit_of_measurement='Amperes',
                precision=None,
                scale='deci',
                description='%s ampere load' % name,
                name=name,
                internal_name='%s%s' % (R_PDU_LOAD_STATUS_LOAD, index),
                mib=self.get_module_name()
            ))
        defer.returnValue(result)

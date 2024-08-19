#
# Copyright (C) 2017 Uninett AS
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
"""MibRetriever implementation for IBM-PDU-MIB"""

from twisted.internet.defer import inlineCallbacks

from nav.mibs import reduce_index
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

PHASE_LAST_POWER_READING = 'ibmPduPhaseLastPowerReading'

OUTLET_NAME = 'ibmPduOutletName'
OUTLET_DESCRIPTION = 'ibmPduOutletDescription'
OUTLET_VOLTAGE = 'ibmPduOutletVoltage'
OUTLET_CURRENT = 'ibmPduOutletCurrent'
OUTLET_MAX_CAPACITY = 'ibmPduOutletMaxCapacity'
OUTLET_LAST_POWER_READING = 'ibmPduOutletLastPowerReading'


class IbmPduMib(MibRetriever):
    """MibRetriever implementation for IBM-PDU-MIB, as used by IBM/Lenovo Power
    Distribution Units.
    """

    mib = get_mib('IBM-PDU-MIB')

    @inlineCallbacks
    def get_all_sensors(self):
        """Retrieves various phase and outlet power usage objects as sensor
        records.
        """
        phases = yield self._get_phase_sensors()
        outlets = yield self._get_outlet_sensors()
        return phases + outlets

    @inlineCallbacks
    def _get_phase_sensors(self):
        phases = yield self.retrieve_columns([PHASE_LAST_POWER_READING]).addCallback(
            reduce_index
        )
        if phases:
            self._logger.debug("Got phase power readings: %r", phases)

        result = []
        column = self.nodes.get(PHASE_LAST_POWER_READING)
        for index, _row in phases.items():
            value_oid = str(column.oid + str(index))
            if len(index) == 2:
                index = index[0]  # PDU agent breaks the MIB definition :P

            name = "Phase %d" % index

            result.append(
                dict(
                    oid=value_oid,
                    unit_of_measurement=Sensor.UNIT_WATTS,
                    precision=0,
                    scale=None,
                    description='%s power reading' % name,
                    name=name,
                    internal_name='%s_%s' % (PHASE_LAST_POWER_READING, index),
                    mib=self.get_module_name(),
                )
            )

        return result

    @inlineCallbacks
    def _get_outlet_sensors(self):
        outlets = yield self.retrieve_columns(
            [
                OUTLET_NAME,
                OUTLET_DESCRIPTION,
                OUTLET_VOLTAGE,
                OUTLET_CURRENT,
                OUTLET_MAX_CAPACITY,
                OUTLET_LAST_POWER_READING,
            ]
        ).addCallback(reduce_index)
        if outlets:
            self._logger.debug("Got outlet power readings: %r", outlets)

        result = []
        for index, row in outlets.items():
            result.extend(self._outlet_row_to_sensors(index, row))

        return result

    def _outlet_row_to_sensors(self, index, row):
        name = row.get(OUTLET_NAME)
        description = row.get(OUTLET_DESCRIPTION)

        voltage = dict(
            oid=str(self.nodes.get(OUTLET_VOLTAGE).oid + str(index)),
            unit_of_measurement=Sensor.UNIT_VOLTS_AC,
            precision=3,
            scale=None,
            description='%s voltage' % description,
            name='%s voltage' % name,
            internal_name='%s_%s' % (OUTLET_VOLTAGE, index),
            mib=self.get_module_name(),
        )
        yield voltage

        current = dict(
            oid=str(self.nodes.get(OUTLET_CURRENT).oid + str(index)),
            unit_of_measurement=Sensor.UNIT_AMPERES,
            precision=3,
            scale=None,
            description='%s current' % description,
            name='%s current' % name,
            internal_name='%s_%s' % (OUTLET_CURRENT, index),
            mib=self.get_module_name(),
        )
        yield current

        power = dict(
            oid=str(self.nodes.get(OUTLET_LAST_POWER_READING).oid + str(index)),
            unit_of_measurement=Sensor.UNIT_WATTS,
            precision=0,
            scale=None,
            description='%s power reading' % description,
            name='%s power reading' % name,
            internal_name='%s_%s' % (OUTLET_LAST_POWER_READING, index),
            mib=self.get_module_name(),
        )
        yield power

# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Uninett AS
# Copyright (C) 2022 Sikt
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
A class that tries to retrieve the most relevant sensors from Powertek PDU.

Uses the vendor-specifica PWT_3Phase_MIBv1_v2.10-MIB to detect and collect
sensor-information.

Please note!
-- not a complete implementation of the mib --

"""

from twisted.internet import defer

from nav.mibs import reduce_index
from nav.smidumps import get_mib
from nav.mibs import mibretriever
from nav.models.manage import Sensor
from nav.oids import OID

# from .itw_mib import for_table


def for_table(table_name):
    """Used for annotating functions to process the returned
    tables"""
    if not hasattr(for_table, 'map'):
        for_table.map = {}

    def decorate(method):
        """Setup link between table and function"""
        for_table.map[table_name] = method.__name__
        return method

    return decorate


class Pwt3PhaseV1Mib(mibretriever.MibRetriever):
    """A class that tries to retrieve all sensors from Powertek PDU"""

    mib = get_mib('PWTv1-MIB')

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

    def _make_result_dict(
        self,
        sensor_oid,
        base_oid,
        serial,
        desc,
        u_o_m=None,
        precision=0,
        scale=None,
        name=None,
    ):
        """Make a simple dictionary to return to plugin"""

        oid = OID(base_oid) + OID(sensor_oid)

        internal_name = str(serial) + desc
        return {
            'oid': oid,
            'unit_of_measurement': u_o_m,
            'precision': precision,
            'scale': scale,
            'description': desc,
            'name': name,
            'internal_name': internal_name,
            'mib': self.get_module_name(),
        }

    @for_table('pduPwrMonitoringInletStatusTable')
    def _get_internal_sensors_params(self, internal_sensors):
        sensors = []

        for sensor in internal_sensors.values():
            serial = sensor.get('inletIndex', None)
            # The spesification says the value can be 0 - 3 but I am
            # seeing 0 - 7 and only 0 has value
            if serial != 0:
                continue

            sensor_oid = sensor.get(0, None)
            name = 'PWT'  # sensor.get('internalName', None)
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletCurrPhase1'),
                    serial,
                    'inletCurrPhase1',
                    precision=1,
                    u_o_m=Sensor.UNIT_AMPERES,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletCurrPhase2'),
                    serial,
                    'inletCurrPhase2',
                    precision=1,
                    u_o_m=Sensor.UNIT_AMPERES,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletCurrPhase3'),
                    serial,
                    'inletCurrPhase3',
                    precision=1,
                    u_o_m=Sensor.UNIT_AMPERES,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletPowerPhase1'),
                    serial,
                    'inletPowerPhase1',
                    precision=1,
                    u_o_m=Sensor.UNIT_WATTS,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletPowerPhase2'),
                    serial,
                    'inletPowerPhase2',
                    precision=1,
                    u_o_m=Sensor.UNIT_WATTS,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletPowerPhase3'),
                    serial,
                    'inletPowerPhase3',
                    precision=1,
                    u_o_m=Sensor.UNIT_WATTS,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletVoltPhase1'),
                    serial,
                    'inletVoltPhase1',
                    precision=1,
                    u_o_m=Sensor.UNIT_VOLTS_AC,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletVoltPhase2'),
                    serial,
                    'inletVoltPhase2',
                    precision=1,
                    u_o_m=Sensor.UNIT_VOLTS_AC,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletVoltPhase3'),
                    serial,
                    'inletVoltPhase3',
                    precision=1,
                    u_o_m=Sensor.UNIT_VOLTS_AC,
                    name=name,
                )
            )
            sensors.append(
                self._make_result_dict(
                    sensor_oid,
                    self._get_oid_for_sensor('inletLoadBalance'),
                    serial,
                    'inletLoadBalance',
                    u_o_m=Sensor.UNIT_PERCENT,
                    name=name,
                )
            )

        return sensors

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Try to retrieve some of the available sensors in this PDU"""
        # We only implement pduPwrMonitoringInletStatusTable for now
        tables = ['pduPwrMonitoringInletStatusTable']

        result = []
        for table in tables:
            self._logger.debug('get_all_sensors: table = %s', table)
            sensors = yield self.retrieve_table(table).addCallback(reduce_index)
            self._logger.debug('get_all_sensors: %s = %s', table, sensors)
            handler = for_table.map.get(table, None)
            if not handler:
                self._logger.error("There is not data handler for %s", table)
            else:
                method = getattr(self, handler)
                result.extend(method(sensors))

        return result

#
# Copyright (C) 2016 Uninett AS
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
"""MibRetriever implementation for Eltek 48V rectifier devices"""

from twisted.internet.defer import inlineCallbacks
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor
from nav.oids import OID

DESIRED_SENSORS = (
    'batteryVoltage',
    'batteryTemp',
    'loadDistributionCurrent',
    'acVoltage1',
    'acVoltage2',
    'acVoltage3',
    'batteryQuality',
    'batteryTimeToDisconnect',
    'loadDistributionBreakerStatus',
)

UNIT_TRANSLATION = {
    '1/100 Volt': {'unit_of_measurement': Sensor.UNIT_VOLTS_DC, 'precision': 2},
    'Volts AC': {'unit_of_measurement': Sensor.UNIT_VOLTS_AC, 'precision': 0},
    'Deg. C/F': {'unit_of_measurement': 'degrees', 'precision': 0},
    'Minutes': {'unit_of_measurement': Sensor.UNIT_MINUTES, 'precision': 0},
}


class EltekDistributedMib(MibRetriever):
    """MibRetriever for ELTEK-DISTRIBUTED-MIB"""

    mib = get_mib('ELTEK-DISTRIBUTED-MIB')

    @inlineCallbacks
    def get_all_sensors(self):
        """Retrieves list of desired and available sensors from the MIB"""
        sensors = []
        for obj in DESIRED_SENSORS:
            sensor = yield self._verify_sensor(obj)
            if sensor:
                sensors.append(sensor)

        return sensors

    @inlineCallbacks
    def _verify_sensor(self, object_name):
        result = yield self.get_next(object_name)
        if result:
            node = self.nodes[object_name]
            oid = node.oid + OID('.0')
            description = node.raw_mib_data.get('description', object_name)
            sensor = {
                'oid': str(oid),
                'internal_name': object_name,
                'name': object_name,
                'description': description,
                'mib': self.mib['moduleName'],
                'scale': None,
            }
            units = node.raw_mib_data.get('units', '')
            sensor['unit_of_measurement'] = units
            for mibunits, navunits in UNIT_TRANSLATION.items():
                if units.lower().startswith(mibunits.lower()):
                    sensor.update(navunits)
            if object_name == 'loadDistributionBreakerStatus':
                sensor['unit_of_measurement'] = Sensor.UNIT_TRUTHVALUE
                sensor['on_state'] = 1
                sensor['on_message'] = "{} alarm".format(description)
                sensor['off_message'] = "{} normal".format(description)
            return sensor

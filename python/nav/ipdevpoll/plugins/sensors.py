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
"""ipdevpoll plugin to collect sensor data.

This plugin uses MibRetriever implementations for various IETF and proprietary
MIBs to discover and store information about physical environmental sensors
available for readout on a device.

"""

from twisted.internet import defer

from nav.mibs.itw_mib import ItWatchDogsMib
from nav.mibs.itw_mibv3 import ItWatchDogsMibV3
from nav.mibs.geist_mibv3 import GeistMibV3
from nav.mibs.cisco_envmon_mib import CiscoEnvMonMib
from nav.mibs.entity_sensor_mib import EntitySensorMib
from nav.mibs.cisco_entity_sensor_mib import CiscoEntitySensorMib

from nav.mibs.mg_snmp_ups_mib import MgSnmpUpsMib
from nav.mibs.p8541_mib import P8541Mib
from nav.mibs.powernet_mib import PowerNetMib
from nav.mibs.spagent_mib import SPAgentMib
from nav.mibs.ups_mib import UpsMib
from nav.mibs.xups_mib import XupsMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

VENDOR_CISCO = 9
VENDOR_HP = 11
# American Power Conversion Corp., APC UPSes
VENDOR_APC = 318
# Emerson Computer Power, Liebert UPSes
VENDOR_EMERSON_COMPUTER_POWER = 476
# Eaton Corporation, Eaton UPSes
VENDOR_EATON = 534
# Merlin Gerin, MGE UPSes
VENDOR_MGE = 705
# IT-Watchdogs (WeatherGoose products), now rebranded as Geist
VENDOR_ITWATCHDOGS = 17373
VENDOR_GEIST = 21239
# Comet
VENDOR_COMET = 22626
VENDOR_AKCP = 3854


class MIBFactory(object):
    """Factory class for producing MibRetriever instances depending on Netbox
    vendors and models.
    """
    @classmethod
    def get_instance(cls, netbox, agent):
        """Returns a list of MibRetriever instances based on Netbox vendors and
        models.
        """
        vendor_id = None
        mibs = None
        if netbox.type:
            vendor_id = netbox.type.get_enterprise_id()
        if vendor_id:
            # Allocate vendor-specific mibs if we know the vendor
            # FIXME: This is horrible, we need a better mechanism.
            if vendor_id == VENDOR_CISCO:
                # Some cisco-boxes may use standard-mib
                mibs = [EntitySensorMib(agent),
                        CiscoEntitySensorMib(agent),
                        CiscoEnvMonMib(agent)]
            elif vendor_id == VENDOR_HP:
                mibs = [EntitySensorMib(agent)]
            elif vendor_id == VENDOR_APC:
                mibs = [PowerNetMib(agent)]
            elif vendor_id == VENDOR_EMERSON_COMPUTER_POWER:
                mibs = [UpsMib(agent)]
            elif vendor_id == VENDOR_EATON:
                mibs = [XupsMib(agent)]
            elif vendor_id == VENDOR_MGE:
                mibs = [MgSnmpUpsMib(agent)]
            elif vendor_id == VENDOR_ITWATCHDOGS:
                # Try with the most recent first
                mibs = [ItWatchDogsMibV3(agent), ItWatchDogsMib(agent)]
            elif vendor_id == VENDOR_GEIST:
                mibs = [GeistMibV3(agent)]
            elif vendor_id == VENDOR_COMET:
                mibs = [P8541Mib(agent)]
            elif vendor_id == VENDOR_AKCP:
                mibs = [SPAgentMib(agent)]
        if not mibs:
            # And then we just sweep up the remains if we could not
            # find a matching vendor.
            mibs = [EntitySensorMib(agent), UpsMib(agent)]
        return mibs


class Sensors(Plugin):
    """Plugin to detect environmental sensors in netboxes"""

    @defer.inlineCallbacks
    def handle(self):
        """Collects sensors and feed them in to persistent store."""
        self._logger.debug('Collection sensors data')
        mibs = MIBFactory.get_instance(self.netbox, self.agent)
        for mib in mibs:
            all_sensors = yield mib.get_all_sensors()
            if len(all_sensors) > 0:
                # Store and jump out on the first MIB that give
                # any results
                self._store_sensors(all_sensors)
                break

    def _store_sensors(self, result):
        """Stores sensor records in the current job's container dictionary, so
        that they may be persisted to the database.

        """
        self._logger.debug('Found %d sensors', len(result))
        sensors = []
        for row in result:
            oid = row.get('oid', None)
            internal_name = row.get('internal_name', None)
            mib = row.get('mib', None)
            # Minimum requirement.  Uniq by netbox, internal name and mib
            if oid and internal_name and mib:
                sensor = self.containers.factory(oid, shadows.Sensor)
                sensor.netbox = self.netbox
                sensor.oid = oid
                sensor.unit_of_measurement = row.get('unit_of_measurement',
                                                     None)
                sensor.precision = row.get('precision', 0)
                sensor.data_scale = row.get('scale', None)
                sensor.human_readable = safestring(row.get('description', None))
                sensor.name = safestring(row.get('name', None))
                sensor.internal_name = safestring(internal_name)
                sensor.mib = mib
                sensors.append(sensors)
        return sensors


ENCODINGS_TO_TRY = ('utf-8', 'latin-1')  # more should be added


def safestring(string):
    """Tries to safely decode strings retrieved using SNMP.

    SNMP does not really define encodings, and will not normally allow
    non-ASCII strings to be written  (though binary data is fine). Sometimes,
    administrators have been able to enter descriptions containing non-ASCII
    characters using CLI's or web interfaces. The encoding of these are
    undefined and unknown. To ensure they can be safely stored in the
    database (which only accepts UTF-8), we make various attempts at decoding
    strings to unicode objects before the database becomes involved.
    """
    if string is None:
        return

    if isinstance(string, unicode):
        return string

    for encoding in ENCODINGS_TO_TRY:
        try:
            return string.decode(encoding)
        except UnicodeDecodeError:
            pass

    return repr(string)  # fallback

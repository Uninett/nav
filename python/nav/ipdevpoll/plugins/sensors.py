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
from nav.mibs.eltek_distributed_mib import EltekDistributedMib

from nav.mibs.mg_snmp_ups_mib import MgSnmpUpsMib
from nav.mibs.comet import Comet
from nav.mibs.powernet_mib import PowerNetMib
from nav.mibs.spagent_mib import SPAgentMib
from nav.mibs.ups_mib import UpsMib
from nav.mibs.xups_mib import XupsMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

from nav.enterprise.ids import (VENDOR_ID_CISCOSYSTEMS,
                                VENDOR_ID_HEWLETT_PACKARD,
                                VENDOR_ID_AMERICAN_POWER_CONVERSION_CORP,
                                VENDOR_ID_EMERSON_COMPUTER_POWER,
                                VENDOR_ID_EATON_CORPORATION,
                                VENDOR_ID_MERLIN_GERIN,
                                VENDOR_ID_IT_WATCHDOGS_INC,
                                VENDOR_ID_GEIST_MANUFACTURING_INC,
                                VENDOR_ID_COMET_SYSTEM_SRO,
                                VENDOR_ID_KCP_INC,
                                VENDOR_ID_ELTEK_ENERGY_AS,
                                )


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
            if vendor_id == VENDOR_ID_CISCOSYSTEMS:
                # Some cisco-boxes may use standard-mib
                mibs = [EntitySensorMib(agent),
                        CiscoEntitySensorMib(agent),
                        CiscoEnvMonMib(agent)]
            elif vendor_id == VENDOR_ID_HEWLETT_PACKARD:
                mibs = [EntitySensorMib(agent)]
            elif vendor_id == VENDOR_ID_AMERICAN_POWER_CONVERSION_CORP:
                mibs = [PowerNetMib(agent)]
            elif vendor_id == VENDOR_ID_EMERSON_COMPUTER_POWER:
                mibs = [UpsMib(agent)]
            elif vendor_id == VENDOR_ID_EATON_CORPORATION:
                mibs = [XupsMib(agent)]
            elif vendor_id == VENDOR_ID_MERLIN_GERIN:
                mibs = [MgSnmpUpsMib(agent)]
            elif vendor_id == VENDOR_ID_IT_WATCHDOGS_INC:
                # Try with the most recent first
                mibs = [ItWatchDogsMibV3(agent), ItWatchDogsMib(agent)]
            elif vendor_id == VENDOR_ID_GEIST_MANUFACTURING_INC:
                mibs = [GeistMibV3(agent)]
            elif vendor_id == VENDOR_ID_COMET_SYSTEM_SRO:
                mibs = [Comet(agent)]
            elif vendor_id == VENDOR_ID_KCP_INC:
                mibs = [SPAgentMib(agent)]
            elif vendor_id == VENDOR_ID_ELTEK_ENERGY_AS:
                mibs = [EltekDistributedMib(agent)]
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

####################
# Helper functions #
####################


def safestring(string, encodings_to_try=('utf-8', 'latin-1')):
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

    for encoding in encodings_to_try:
        try:
            return string.decode(encoding)
        except UnicodeDecodeError:
            pass

    return repr(string)  # fallback

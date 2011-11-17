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
"""ipdevpoll plugin to collect sensor data.

This plugin use CISCO-ENVMON-MIB, ENTITY-SENSOR-MIB and IT-WATCHDOGS-MIB-V3
to retrieve all possible sensors in network-equipment.
"""

from twisted.internet import defer

from nav.mibs.itw_mib import ItWatchDogsMib
from nav.mibs.itw_mibv3 import ItWatchDogsMibV3
from nav.mibs.cisco_envmon_mib import CiscoEnvMonMib
from nav.mibs.entity_sensor_mib import EntitySensorMib

from nav.mibs.mg_snmp_ups_mib import MgSnmpUpsMib
from nav.mibs.powernet_mib import PowerNetMib
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
# IT-Watchdogs,- i.e. WxGooses
VENDOR_ITWATCHDOGS = 17373


class MIBFactory(object):
    """A class that produces mibs depending and netbox-vendors
    and -models."""

    @classmethod
    def get_instance(cls, netbox, agent):
        """ Factory for allocating mibs based on
        netbox-vendors and -models"""
        vendor_id = None
        if netbox.type:
            vendor_id = netbox.type.get_enterprise_id()
        if vendor_id:
            if vendor_id == VENDOR_CISCO:
                # Some cisco-boxes may use standard-mib
                return [EntitySensorMib(agent), CiscoEnvMonMib(agent)]
            elif vendor_id == VENDOR_HP:
                return [EntitySensorMib(agent)]
            elif vendor_id == VENDOR_APC:
                return [PowerNetMib(agent)]
            elif vendor_id == VENDOR_EMERSON_COMPUTER_POWER:
                return [UpsMib(agent)]
            elif vendor_id == VENDOR_EATON:
                return [XupsMib(agent)]
            elif vendor_id == VENDOR_MGE:
                return [MgSnmpUpsMib(agent)]
            elif vendor_id == VENDOR_ITWATCHDOGS:
                # Try with the most recent first
                return [ItWatchDogsMibV3(agent), ItWatchDogsMib(agent)]
        # and then we just sweep up the remains....
        return [EntitySensorMib(agent), UpsMib(agent)]


class Sensors(Plugin):
    """ Plugin that detect sensors in netboxes."""

    @classmethod
    def can_handle(cls, netbox):
        return True

    @defer.inlineCallbacks
    def handle(self):
        """ Collect sensors and feed them in to persistent store."""
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
        """ Store sensor-records to database (this is actually
            done automagically when we use shadow-objects."""
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
                sensor.human_readable = row.get('description', None)
                sensor.name = row.get('name', None)
                sensor.internal_name = internal_name
                sensor.mib = mib
                sensors.append(sensors)
        return sensors

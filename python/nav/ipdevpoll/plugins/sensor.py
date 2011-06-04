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

from nav.mibs import reduce_index
from nav.mibs.itw_mibv3 import ItWatchDogsMibV3
from nav.mibs.cisco_envmon_mib import CiscoEnvMonMib
from nav.mibs.entity_sensor_mib import EntitySensorMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.ipdevpoll.utils import binary_mac_to_hex

VENDOR_CISCO = 9
VENDOR_HP = 11
VENDOR_ITWATCHDOGS = 17373

class Sensor(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self._logger.debug("Collecting sensor data")
        self.it_watch_dogs_mibv3 = ItWatchDogsMibV3(self.agent)
        self.cisco_envmon_mib = CiscoEnvMonMib(self.agent)
        self.entity_sensor_mib = EntitySensorMib(self.agent)

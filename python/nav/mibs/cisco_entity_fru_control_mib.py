#
# Copyright 2008 - 2011, 2019 (C) Uninett AS
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
"""
A class that collects the oids for fan- and psu-sensors,- and their
corresponding fan- and psu-statuses.

The class is specific for CISCO netboxes and use the
CISCO-ENTITY-FRU-CONTROL-MIB to collect sensor-oids and read statuses.
"""

from twisted.internet import defer

from nav.mibs.entity_mib import EntityMib
from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index

from nav.models.manage import PowerSupplyOrFan


FAN_STATUS_MAP = {
    "unknown": PowerSupplyOrFan.STATE_UNKNOWN,
    "up": PowerSupplyOrFan.STATE_UP,
    "down": PowerSupplyOrFan.STATE_DOWN,
    "warning": PowerSupplyOrFan.STATE_WARNING,
}


PSU_STATUS_MAP = {
    "offEnvOther": PowerSupplyOrFan.STATE_DOWN,
    "on": PowerSupplyOrFan.STATE_UP,
    "offAdmin": PowerSupplyOrFan.STATE_DOWN,
    "offDenied": PowerSupplyOrFan.STATE_DOWN,
    "offEnvPower": PowerSupplyOrFan.STATE_DOWN,
    "offEnvTemp": PowerSupplyOrFan.STATE_DOWN,
    "offEnvFan": PowerSupplyOrFan.STATE_DOWN,
    "failed": PowerSupplyOrFan.STATE_DOWN,
    "onButFanFail": PowerSupplyOrFan.STATE_WARNING,
    "offCooling": PowerSupplyOrFan.STATE_DOWN,
    "offConnectorRating": PowerSupplyOrFan.STATE_DOWN,
    "onButInlinePowerFail": PowerSupplyOrFan.STATE_DOWN,
}


class CiscoEntityFruControlMib(mibretriever.MibRetriever):
    """A MibRetriever to collect inventory and status information for
    field-replaceable units (such as power supplies and fans) on Cisco netboxes.

    """

    mib = get_mib("CISCO-ENTITY-FRU-CONTROL-MIB")

    def __init__(self, agent_proxy):
        super(CiscoEntityFruControlMib, self).__init__(agent_proxy)
        self.entity_mib = EntityMib(self.agent_proxy)
        self.fan_status_table = None
        self.psu_status_table = None

    def _get_fantray_status_table(self):
        """Retrieve the whole table of fan-sensors."""
        return self.retrieve_table("cefcFanTrayStatusTable").addCallback(reduce_index)

    def _get_power_status_table(self):
        """Retrieve the whole table of PSU-sensors."""
        self.retrieve_table("cefcFRUPowerStatusTable").addCallback(reduce_index)

    @staticmethod
    def _translate_fan_status(oper_status):
        """Translates the fan status value from the MIB to a NAV PSU status value.

        :returns: A state value from nav.models.manage.PowerSupplyOrFan.STATE_CHOICES

        """
        return FAN_STATUS_MAP.get(oper_status, PowerSupplyOrFan.STATE_UNKNOWN)

    @staticmethod
    def _translate_power_supply_status_value(oper_status):
        """Translates the PSU status value from the MIB to a NAV PSU status value.

        :returns: A state value from nav.models.manage.PowerSupplyOrFan.STATE_CHOICES

        """
        return PSU_STATUS_MAP.get(oper_status, PowerSupplyOrFan.STATE_UNKNOWN)

    @defer.inlineCallbacks
    def get_fan_status(self, internal_id):
        """Returns the operational status for a fan with the given internal id."""
        oper_status = yield self.retrieve_column_by_index(
            "cefcFanTrayOperStatus", (int(internal_id),)
        )
        self._logger.debug("cefcFanTrayOperStatus.%s = %r", internal_id, oper_status)
        return self._translate_fan_status(oper_status)

    @defer.inlineCallbacks
    def get_power_supply_status(self, internal_id):
        """Returns the operational status for a PSU with the given internal id."""
        oper_status = yield self.retrieve_column_by_index(
            "cefcFRUPowerOperStatus", (int(internal_id),)
        )
        self._logger.debug("cefcFRUPowerOperStatus.%s = %r", internal_id, oper_status)
        return self._translate_power_supply_status_value(oper_status)

    @defer.inlineCallbacks
    def get_fan_status_table(self):
        """Retrieve the whole table of fan-sensors and cache the result."""
        if not self.fan_status_table:
            self.fan_status_table = yield self._get_fantray_status_table()
        return self.fan_status_table

    @defer.inlineCallbacks
    def get_psu_status_table(self):
        """Retrieve the whole table of PSU-sensors and cache the result."""
        if not self.psu_status_table:
            self.psu_status_table = yield self._get_power_status_table()
        return self.psu_status_table

    def get_power_supplies(self):
        """Retrieves a list of power supply objects"""
        return self.entity_mib.get_power_supplies()

    @defer.inlineCallbacks
    def get_fans(self):
        """Retrieves a list of fan objects.

        A Cisco device reports fan trays and individual fans in entPhysicalTable,
        but only the status of entire fan trays can be queried from this MIB,
        so this filters away any non-FRU units.
        """
        fans = yield self.entity_mib.get_fans()
        status = yield self.get_fan_status_table()
        self._logger.debug(
            "found %d/%d field-replaceable fan entities", len(status), len(fans)
        )
        fans = [fan for fan in fans if fan.internal_id in status]
        return fans

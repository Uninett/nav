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
"""Implements a MibRetriever for Hewlett Packard's FAN-MIB."""

from operator import attrgetter

from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs.entity_mib import EntityMib
from nav.smidumps import get_mib
from nav.mibs import mibretriever

from nav.models.manage import PowerSupplyOrFan as FAN
from .hpicf_powersupply_mib import (
    _psu_index_from_internal_id as _fan_index_from_internal_id,
)


FAN_STATUS_MAP = {
    "failed": FAN.STATE_DOWN,
    "removed": FAN.STATE_UNKNOWN,
    "off": FAN.STATE_UNKNOWN,
    "underspeed": FAN.STATE_WARNING,
    "overspeed": FAN.STATE_WARNING,
    "ok": FAN.STATE_UP,
    "maxstate": FAN.STATE_WARNING,
}


class HpIcfFanMib(mibretriever.MibRetriever):
    """A MibRetriever for collecting fan states from HP netboxes."""

    mib = get_mib("FAN-MIB")

    def __init__(self, agent_proxy):
        super(HpIcfFanMib, self).__init__(agent_proxy)
        self.entity_mib = EntityMib(agent_proxy)
        self.fan_status_table = None

    @defer.inlineCallbacks
    def _get_fan_status_table(self):
        """Returns the fan status from this netbox."""
        df = self.retrieve_table("hpicfFanTable")
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        fan_table = yield df
        self._logger.debug("fan_table: %r", fan_table)
        return fan_table

    @staticmethod
    def _translate_fan_status(psu_status):
        """Translates the PSU status value from the MIB to a NAV PSU status value.

        :returns: A state value from nav.models.manage.PowerSupplyOrFan.STATE_CHOICES

        """
        return FAN_STATUS_MAP.get(psu_status, FAN.STATE_UNKNOWN)

    @defer.inlineCallbacks
    def get_fan_status(self, internal_id):
        """Returns the status of the fan with the given internal id."""
        if not self.fan_status_table:
            self.fan_status_table = yield self._get_fan_status_table()

        index = _fan_index_from_internal_id(internal_id)
        fan_status_row = self.fan_status_table.get(index, {})
        fan_status = fan_status_row.get("hpicfFanState")

        self._logger.debug("hpicfFanState.%s = %r", index, fan_status)
        return self._translate_fan_status(fan_status)

    @defer.inlineCallbacks
    def get_fans(self):
        """Retrieves a list of fan objects"""
        hp_fans = yield self._get_fan_status_table()
        entities = yield self.entity_mib.get_fans()
        if len(hp_fans) != len(entities):
            self._logger.warning(
                "Number of fans in ENTITY-MIB (%d) and FAN-MIB (%d) do not match",
                len(entities),
                len(hp_fans),
            )

        # Fans always numbered from 1 and up in FAN-MIB,
        # and there is no official way to map their IDs to
        # ENTITY-MIB::entPhysicalTable - therefore, this code naively assumes they at
        # least appear in the same order in the two MIBS
        for index, ent in enumerate(
            sorted(entities, key=attrgetter("internal_id")), start=1
        ):
            ent.internal_id = "{}:{}".format(ent.internal_id, index)

        return entities

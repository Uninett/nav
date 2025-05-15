#
# Copyright 2008 - 2011, 2014, 2019 (C) Uninett AS
# Copyright (C) 2022 Sikt
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
"""Implements a MibRetriever for Hewlett Packard's POWERSUPPLY-MIB."""

from operator import attrgetter

from twisted.internet import defer

from nav.mibs import reduce_index
from nav.mibs.entity_mib import EntityMib
from nav.smidumps import get_mib
from nav.mibs import mibretriever

from nav.models.manage import PowerSupplyOrFan as PSU


PSU_STATUS_MAP = {
    "psPowered": PSU.STATE_UP,
    "psNotPlugged": PSU.STATE_DOWN,
    "psFailed": PSU.STATE_DOWN,
    "psPermFailure": PSU.STATE_DOWN,
    "psMax": PSU.STATE_WARNING,
}


class HpIcfPowerSupplyMib(mibretriever.MibRetriever):
    """A MibRetriever for collecting power supply states from HP netboxes."""

    mib = get_mib("POWERSUPPLY-MIB")

    def __init__(self, agent_proxy):
        super(HpIcfPowerSupplyMib, self).__init__(agent_proxy)
        self.entity_mib = EntityMib(agent_proxy)
        self.psu_status_table = None

    @defer.inlineCallbacks
    def _get_psu_status_table(self):
        """Returns the power supply status table from this netbox."""
        df = self.retrieve_table("hpicfPsTable")
        df.addCallback(self.translate_result)
        df.addCallback(reduce_index)
        psu_table = yield df
        self._logger.debug("psu_table: %r", psu_table)
        return psu_table

    @staticmethod
    def _translate_psu_status(psu_status):
        """Translates the PSU status value from the MIB to a NAV PSU status value.

        :returns: A state value from nav.models.manage.PowerSupplyOrFan.STATE_CHOICES

        """
        return PSU_STATUS_MAP.get(psu_status, PSU.STATE_UNKNOWN)

    @defer.inlineCallbacks
    def get_power_supply_status(self, internal_id):
        """Returns the status of the powersupply with the given internal id."""
        if not self.psu_status_table:
            self.psu_status_table = yield self._get_psu_status_table()

        index = _psu_index_from_internal_id(internal_id)
        psu_status_row = self.psu_status_table.get(index, {})
        psu_status = psu_status_row.get("hpicfPsState")

        self._logger.debug("hpicfPsState.%s = %r", index, psu_status)
        return self._translate_psu_status(psu_status)

    @defer.inlineCallbacks
    def get_power_supplies(self):
        """Retrieves a list of power supply objects"""
        hp_psus = yield self._get_psu_status_table()
        entities = yield self.entity_mib.get_power_supplies()
        if len(hp_psus) != len(entities):
            self._logger.warning(
                "Number of power supplies in ENTITY-MIB (%d) and POWERSUPPLY-MIB (%d) "
                "do not match",
                len(entities),
                len(hp_psus),
            )

        # Power supplies are always numbered from 1 and up in POWERSUPPLY-MIB,
        # and there is no official way to map their IDs to
        # ENTITY-MIB::entPhysicalTable - therefore, this code naively assumes they at
        # least appear in the same order in the two MIBS
        for index, ent in enumerate(
            sorted(entities, key=attrgetter("internal_id")), start=1
        ):
            ent.internal_id = "{}:{}".format(ent.internal_id, index)

        return entities


def _psu_index_from_internal_id(internal_id):
    if isinstance(internal_id, str):
        return int(internal_id.split(":")[1] if ":" in internal_id else internal_id)
    else:
        return internal_id

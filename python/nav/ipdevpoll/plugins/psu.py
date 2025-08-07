#
# Copyright (C) 2008-2011, 2014, 2019 Uninett AS
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
"""This ipdevpoll plugin collects the inventory of power supplies and fans from
devices.

The inventory record of a PSU or FAN includes an SNMP OID that can be used to monitor
the status of the entity by the powersupplywatch program. Normally, this status
information is not available in the ENTITY-MIB itself, but from some proprietary MIB.
This plugin tries to discover the relationship between PSU/FAN entities found in
ENTITY-MIB and entities found in the proprietary MIBs.

At the moment, only Cisco and Hewlett-Packard devices are supported, but support for
new vendors can be added by creating new MibRetriever class which implements the
necessary interfaces to fetch lists of PSU or FAN units, and to to query their states.

See the implementations of these methods in the currently supported MibRetriever
instances for Cisco and HP:


- get_power_supplies()
- get_fans()
- get_power_supply_status()
- get_fan_status()

"""

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

from nav.mibs.entity_mib import EntityMib
from nav.mibs.cisco_entity_fru_control_mib import CiscoEntityFruControlMib
from nav.mibs.hpicf_fan_mib import HpIcfFanMib
from nav.mibs.hpicf_powersupply_mib import HpIcfPowerSupplyMib
from nav.mibs.juniper_mib import JuniperMib
from nav.enterprise.ids import (
    VENDOR_ID_CISCOSYSTEMS,
    VENDOR_ID_HEWLETT_PACKARD,
    VENDOR_ID_JUNIPER_NETWORKS_INC,
)

VENDOR_MIB_MAP = {
    VENDOR_ID_CISCOSYSTEMS: [CiscoEntityFruControlMib],
    VENDOR_ID_HEWLETT_PACKARD: [HpIcfPowerSupplyMib, HpIcfFanMib],
    VENDOR_ID_JUNIPER_NETWORKS_INC: [JuniperMib],
}
FALLBACK_MIBS = [EntityMib]


class PowerSupplyUnit(Plugin):
    """Plugin that collect PSUs and FANs,- and their status from netboxes."""

    def __init__(self, *args, **kwargs):
        super(PowerSupplyUnit, self).__init__(*args, **kwargs)
        self.vendor_id = (
            self.netbox.type.get_enterprise_id() if self.netbox.type else None
        )
        self.miblist = get_mibretrievers_from_vendor_id(self.vendor_id, self.agent)

    @defer.inlineCallbacks
    def handle(self):
        """
        Collect PSUs and FANs,- their corresponding statuses and store in database.
        """
        self._logger.debug("Collecting PSUs and FANs")
        psus = []
        fans = []
        for mib in self.miblist:
            if hasattr(mib, "get_power_supplies"):
                _psus = yield mib.get_power_supplies()
                if _psus:
                    psus.extend(_psus)

            if hasattr(mib, "get_fans"):
                _fans = yield mib.get_fans()
                if _fans:
                    psus.extend(_fans)

        # for now, the data model is the same for both PSUs and FANs, so:
        all_the_things = psus + fans
        if all_the_things:
            for unit in all_the_things:
                yield self._handle_unit(unit)

    def _handle_unit(self, in_unit):
        """
        :type in_unit: nav.ipdevpoll.shadows.PowerSupplyOrFan
        """
        self._logger.debug("PSU:FAN: %s", in_unit)

        out_unit = self.containers.factory(in_unit.name, shadows.PowerSupplyOrFan)
        out_unit.copy(in_unit)
        out_unit.netbox = self.netbox

        if in_unit.device:
            device = self.containers.factory(in_unit.device.serial, shadows.Device)
            device.copy(in_unit.device)
            out_unit.device = device


def get_mibretrievers_from_vendor_id(vendor_id, agent_proxy):
    """Returns a list of matching MibRetriever instances based on a vendor id.
    :param vendor_id: A integer IANA enterprise number.
    :param agent_proxy: An SNMP agent_proxy instance.

    """
    miblist = VENDOR_MIB_MAP.get(vendor_id, FALLBACK_MIBS)
    return [mibclass(agent_proxy) for mibclass in miblist]

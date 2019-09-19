#
# Copyright (C) 2013 Uninett AS
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
"""JUNIPER-MIB MibRetriever"""
from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.ipdevpoll.shadows import PowerSupplyOrFan, Device


OPERATING_DESCR = "jnxOperatingDescr"
OPERATING_CPU = "jnxOperatingCPU"
LOAD_AVG_1MIN = "jnxOperating1MinLoadAvg"
LOAD_AVG_5MIN = "jnxOperating1MinLoadAvg"
LOAD_AVG_15MIN = "jnxOperating1MinLoadAvg"


class JuniperMib(MibRetriever):
    """JUNIPER-MIB MibRetriever"""

    mib = get_mib("JUNIPER-MIB")

    @defer.inlineCallbacks
    def get_serial_number(self):
        """Tries to get a serial number from a Juniper device"""
        serial = yield self.get_next("jnxBoxSerialNo")
        if serial:
            defer.returnValue(serial)

    @defer.inlineCallbacks
    def get_cpu_loadavg(self):
        """Retrieves load averages for various operating subjects in a Juniper
        device.

        BUGS: Juniper's MIB definition is b0rked, as it says that a load
        value of 0 means that the load value is either unavailable or
        not applicable, which makes it indistinguishable from an actual value
        of 0.

        """
        load = yield self.retrieve_columns(
            [OPERATING_DESCR, LOAD_AVG_1MIN, LOAD_AVG_5MIN, LOAD_AVG_15MIN]
        )

        if load:
            result = dict()
            for row in load.values():
                if row[LOAD_AVG_15MIN] or row[LOAD_AVG_5MIN] or row[LOAD_AVG_1MIN]:
                    name = row[OPERATING_DESCR]
                    values = [
                        (15, row[LOAD_AVG_15MIN]),
                        (5, row[LOAD_AVG_5MIN]),
                        (1, row[LOAD_AVG_1MIN]),
                    ]
                    result[name] = values
            defer.returnValue(result)

    @defer.inlineCallbacks
    def get_cpu_utilization(self):
        """Retrieves CPU utilization values for various operating subjects in
        a Juniper device.

        BUGS: Juniper's MIB definition is b0rked, as it says that a CPU
        utilization value of 0 means that the value is either unavailable or
        not applicable, which makes it indistinguishable from an actual value
        of 0.

        """
        util = yield self.retrieve_columns([OPERATING_DESCR, OPERATING_CPU])

        if util:
            result = dict()
            for row in util.values():
                if row[OPERATING_CPU]:
                    name = row[OPERATING_DESCR]
                    result[name] = row[OPERATING_CPU]
            defer.returnValue(result)

    def get_power_supplies(self):
        """Retrieves a list of field-replaceable power supply units"""
        return self._get_fru_by_type("powerEntryModule")

    def get_fans(self):
        """Retrieves a list of field-replaceable fan units"""
        return self._get_fru_by_type("fan")

    @defer.inlineCallbacks
    def _get_fru_by_type(self, fru_type):
        # Columns from two different, but related tables:
        response = yield self.retrieve_columns(
            [
                "jnxFruName",
                "jnxFruType",
                "jnxFruState",
                "jnxContentsSerialNo",
                "jnxContentsModel",
            ]
        ).addCallback(self.translate_result)
        self._logger.warning("jnxFru results: %r", response)
        units = [
            _fru_row_to_powersupply_or_fan(row)
            for row in response.values()
            if row.get("jnxFruState") != "empty" and row.get("jnxFruType") == fru_type
        ]
        defer.returnValue(units)


def _fru_row_to_powersupply_or_fan(fru_row):
    model = fru_row.get("jnxContentsModel")
    psu_or_fan = PowerSupplyOrFan(
        name=fru_row.get("jnxFruName"),
        physical_class="powerSupply"
        if fru_row.get("jnxFruType") == "powerEntryModule"
        else "fan",
        descr=model,
        internal_id=fru_row.get(0),
    )
    serial = fru_row.get("jnxContentsSerialNo")
    if serial:
        device = Device(serial=serial)
        if model:
            device.model = model
        psu_or_fan.device = device
    return psu_or_fan

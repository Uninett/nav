#
# Copyright (C) 2013 Uninett AS
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
"""JUNIPER-MIB MibRetriever"""

from twisted.internet import defer

from nav.oids import OID
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.mibs import reduce_index
from nav.models.manage import PowerSupplyOrFan as FRU
from nav.ipdevpoll.shadows import PowerSupplyOrFan, Device
from nav.models.manage import Sensor

MEGABYTE = 1024**2

OPERATING_DESCR = "jnxOperatingDescr"
OPERATING_CPU = "jnxOperatingCPU"
LOAD_AVG_1MIN = "jnxOperating1MinLoadAvg"
LOAD_AVG_5MIN = "jnxOperating5MinLoadAvg"
LOAD_AVG_15MIN = "jnxOperating15MinLoadAvg"
OPERATING_MEM = "jnxOperatingMemory"
OPERATING_BUF = "jnxOperatingBuffer"

FRU_STATUS_MAP = {
    "unknown": FRU.STATE_UNKNOWN,
    "empty": FRU.STATE_UNKNOWN,
    "present": FRU.STATE_UNKNOWN,
    "ready": FRU.STATE_UNKNOWN,
    "announceOnline": FRU.STATE_UNKNOWN,
    "online": FRU.STATE_UP,
    "anounceOffline": FRU.STATE_WARNING,
    "offline": FRU.STATE_DOWN,
    "diagnostic": FRU.STATE_WARNING,
    "standby": FRU.STATE_WARNING,
}

SENSOR_TABLES = {
    'jnxOperatingTable': {
        'descr': 'jnxOperatingDescr',
        'unit': Sensor.UNIT_CELSIUS,
        'readout': 'jnxOperatingTemp',
        'internal_prefix': 'temperature',
    },
}


class JuniperMib(MibRetriever):
    """JUNIPER-MIB MibRetriever"""

    mib = get_mib("JUNIPER-MIB")

    @defer.inlineCallbacks
    def get_serial_number(self):
        """Tries to get a serial number from a Juniper device"""
        serial = yield self.get_next("jnxBoxSerialNo")
        if serial:
            if isinstance(serial, bytes):
                serial = serial.decode("utf-8")
            return serial

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
            return result

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
            return result

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
        self._logger.debug("jnxFru results: %r", response)
        units = [
            _fru_row_to_powersupply_or_fan(row)
            for row in response.values()
            if row.get("jnxFruState") != "empty" and row.get("jnxFruType") == fru_type
        ]
        return units

    @defer.inlineCallbacks
    def get_fru_status(self, internal_id):
        """Returns the operational status for a FRU with the given internal id."""
        oper_status = yield self.retrieve_column_by_index(
            "jnxFruState", OID(internal_id)
        )
        self._logger.debug("jnxFruState.%s = %r", internal_id, oper_status)
        return self._translate_fru_status_value(oper_status)

    get_fan_status = get_fru_status
    get_power_supply_status = get_fru_status

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Returns a Deferred whose result is a list of sensor dictionaries"""
        result = []
        for table, config in SENSOR_TABLES.items():
            sensors = yield self._get_sensors(config)
            result.extend(sensors)
        return result

    @defer.inlineCallbacks
    def _get_sensors(self, config):
        """
        Collects sensor columns according to the config dict, and translates
        the results into sensor dicts.

        """
        columns = [config['descr'], config['readout']]

        result = (
            yield self.retrieve_columns(columns)
            .addCallback(self.translate_result)
            .addCallback(reduce_index)
        )

        sensors = (
            self._row_to_sensor(config, index, row) for index, row in result.items()
        )

        return [s for s in sensors if s]

    def _row_to_sensor(self, config, index, row):
        """
        Converts a collect SNMP table row into a sensor dict, using the
        options defined in the config dict.

        """
        # Dont include sensor if temperature not set
        readout = row.get(config['readout'], 0)
        if not readout:
            return

        internal_name = config['internal_prefix'] + str(index)
        descr = row.get(config['descr'], internal_name) + " Temperature"

        mibobject = self.nodes.get(config['readout'])
        readout_oid = str(mibobject.oid + str(index))

        return {
            'oid': readout_oid,
            'unit_of_measurement': config['unit'],
            'precision': 0,
            'scale': None,
            'description': descr,
            'name': descr,
            'internal_name': internal_name,
            'mib': self.get_module_name(),
        }

    @staticmethod
    def _translate_fru_status_value(oper_status):
        """Translates the FRU status value from the MIB to a NAV PSU status value.

        :returns: A state value from nav.models.manage.PowerSupplyOrFan.STATE_CHOICES

        """
        return FRU_STATUS_MAP.get(oper_status, FRU.STATE_UNKNOWN)

    @defer.inlineCallbacks
    def get_memory_usage(self):
        """Retrieves memory usage stats from a Juniper device.

        :returns: A deferred whose result is a dict
                  {slot_type: (used_bytes, free_bytes)}

        """
        result = dict()
        slots = yield self.retrieve_columns(
            [OPERATING_DESCR, OPERATING_MEM, OPERATING_BUF]
        )
        for row in slots.values():
            total = row[OPERATING_MEM] * MEGABYTE
            if total:
                used = (row[OPERATING_BUF] / 100) * total
                free = total - used
                result[row[OPERATING_DESCR]] = (used, free)
        return result


def _fru_row_to_powersupply_or_fan(fru_row):
    model = fru_row.get("jnxContentsModel")
    psu_or_fan = PowerSupplyOrFan(
        name=fru_row.get("jnxFruName"),
        physical_class=(
            "powerSupply" if fru_row.get("jnxFruType") == "powerEntryModule" else "fan"
        ),
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

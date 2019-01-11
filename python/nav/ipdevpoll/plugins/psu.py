#
# Copyright (C) 2008-2011, 2014 Uninett AS
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
"""
ipdevpolld-plugin to collect powersupply units and fans,- and their
corresponding status.  For the time beeing this plugin is only able
to collect powersupplies and fans from Cisco- and HP-netboxes.

This plugin uses ENTITY-MIB to retrieve all possible PSUs in network-
equipment.

Status for PSUs and FANs in Cisco-equipment are collected with
CISCO-ENTITY-FRU-CONTROL-MIB.

Status for PSUs and FANs in HP-equipment are collected with POWERSUPPLY-MIB
and FAN-MIB from HP's support pages.
"""
from operator import itemgetter

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

from nav.mibs.entity_mib import EntityMib, EntityTable

from nav.mibs.cisco_entity_fru_control_mib import CiscoEntityFruControlMib
from nav.mibs.hp_entity_fru_control_mib import HpEntityFruControlMib
from nav.enterprise.ids import (VENDOR_ID_CISCOSYSTEMS,
                                VENDOR_ID_HEWLETT_PACKARD,
                                )


class PowerSupplyUnit(Plugin):
    """Plugin that collect PSUs and FANs,- and their status from netboxes."""
    vendor_id = None

    def __init__(self, *args, **kwargs):
        """ Constructor..."""
        super(PowerSupplyUnit, self).__init__(*args, **kwargs)
        self.entity_mib = EntityMib(self.agent)
        self.entity_fru_control = None
        self.vendor_id = None
        if self.netbox.type:
            self.vendor_id = self.netbox.type.get_enterprise_id()
        if self.vendor_id == VENDOR_ID_CISCOSYSTEMS:
            self.entity_fru_control = CiscoEntityFruControlMib(self.agent)
        elif self.vendor_id == VENDOR_ID_HEWLETT_PACKARD:
            self.entity_fru_control = HpEntityFruControlMib(self.agent)

    @staticmethod
    def _enumerate_entities(entities):
        """Enumerate and annotate entities according to their internal order,
        for looking up the entities in private HP MIBs.

        This makes the very naive assumption that fans and power supplies are
        listed in the same order in entPhysicalTable as in the private HP
        mibs for fans and power supplies.
        """
        entities.sort(key=itemgetter(0))
        for index, ent in enumerate(entities, start=1):
            ent['_internal_index'] = index
        return entities

    def _get_psus_and_fans(self, to_filter):
        """Extracts only fans and power supplies from a list of entities"""
        power_supplies = []
        fans = []
        for unit in to_filter.values():
            if self.is_psu(unit):
                power_supplies.append(unit)
            if self.is_fan(unit):
                fans.append(unit)
        if self.vendor_id and self.vendor_id == VENDOR_ID_HEWLETT_PACKARD:
            # Index-numbers from HP-netboxes need to be re-numbered to match
            # index-numbers in POWERSUPPLY-MIB and FAN-MIB.
            # Index-numbers should in practice start at 1 for both PSUs and
            # FANs to match the corresponding statuses.
            self._enumerate_entities(power_supplies)
            self._enumerate_entities(fans)

        # Create list of all psus and fans.  Add all psus first.
        all_psus_and_fans = power_supplies
        # Then add all fans.
        all_psus_and_fans.extend(fans)
        return all_psus_and_fans

    @staticmethod
    def is_fan(pwr):
        """Determine if this unit is a fan"""
        return pwr.get('entPhysicalClass', None) == 'fan'

    @staticmethod
    def is_psu(pwr):
        """Determine if this unit is a powersupply"""
        return pwr.get('entPhysicalClass', None) == 'powerSupply'

    @defer.inlineCallbacks
    def handle(self):
        """Collect PSUs and FANs,- their corresponding statuses and store
        in database"""
        self._logger.debug("Collecting PSUs and FANs")

        entity_table = yield self.entity_mib.get_useful_physical_table_columns()
        entity_table = EntityTable(entity_table)
        psus_and_fans = self._get_psus_and_fans(entity_table)
        if psus_and_fans:
            for psu_or_fan in psus_and_fans:
                yield self._handle_unit(psu_or_fan)

    @defer.inlineCallbacks
    def _handle_unit(self, psu_or_fan):
        self._logger.debug('PSU:FAN: %s', psu_or_fan)
        internal_index = psu_or_fan.get('_internal_index', psu_or_fan.get(0))
        is_up = 'u'
        sensor_oid = None
        control = self.entity_fru_control
        if not control:
            defer.returnValue(None)

        if self.is_fan(psu_or_fan):
            # locate sensor and get status
            ret = yield control.is_fan_up(internal_index)
            if ret:
                is_up = ret
                sensor_oid = control.get_oid_for_fan_status(internal_index)
            self._logger.debug('FAN: %s: %s', ret, sensor_oid)
        elif self.is_psu(psu_or_fan):
            ret = yield control.is_psu_up(internal_index)
            if ret:
                is_up = ret
                sensor_oid = control.get_oid_for_psu_status(internal_index)
            self._logger.debug('PSU: %s: %s', ret, sensor_oid)
        phys_name = psu_or_fan.get('entPhysicalName', None)

        power_supply = self.containers.factory(phys_name,
                                               shadows.PowerSupplyOrFan)
        # psu info
        power_supply.netbox = self.netbox
        power_supply.name = phys_name
        power_supply.model = psu_or_fan.get('entPhysicalModelName', None)
        power_supply.descr = psu_or_fan.get('entPhysicalDescr', None)
        power_supply.physical_class = psu_or_fan.get('entPhysicalClass', None)
        power_supply.sensor_oid = sensor_oid
        power_supply.up = is_up
        # device info
        serial = psu_or_fan.get('entPhysicalSerialNum', None)
        if serial:
            device = self.containers.factory(serial, shadows.Device)
            device.serial = serial
            device.hardware_version = psu_or_fan.get('entPhysicalHardwareRev',
                                                     None)
            device.firmware_version = psu_or_fan.get('entPhysicalFirmwareRev',
                                                     None)
            device.software_version = psu_or_fan.get('entPhysicalSoftwareRev',
                                                     None)
            power_supply.device = device

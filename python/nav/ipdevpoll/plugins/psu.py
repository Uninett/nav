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

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

from nav.mibs.entity_mib import EntityMib, EntityTable

from nav.mibs.cisco_entity_fru_control_mib import CiscoEntityFruControlMib
from nav.mibs.hp_entity_fru_control_mib import HpEntityFruControlMib

VENDOR_CISCO = 9
VENDOR_HP = 11


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
        if self.vendor_id == VENDOR_CISCO:
            self.entity_fru_control = CiscoEntityFruControlMib(self.agent)
        elif self.vendor_id == VENDOR_HP:
            self.entity_fru_control = HpEntityFruControlMib(self.agent)

    def _get_lowest_index(self, values):
        """Return the lowest index in the list of dicts.  Index is placed at
        key 0 in the dicts"""
        lowest_index = 2147483647L
        for val in values:
            curr_idx = val.get(0, None)
            if curr_idx < lowest_index:
                lowest_index = curr_idx
        return lowest_index

    def _rearrange_indexes(self, values):
        """Rearrange indexes down to the lowest possible number"""
        lowest_index = self._get_lowest_index(values)
        # First index must start at 1.
        lowest_index -= 1
        if lowest_index < 0:
            lowest_index = 0
        for val in values:
            curr_idx = val.get(0, None)
            val[0] = curr_idx - lowest_index
        return values

    def _get_psus_and_fans(self, to_filter):
        """ Filter out PSUs and FANs, and return only redundant."""
        power_supplies = []
        fans = []
        for unit in  to_filter.values():
            if self.is_psu(unit):
                power_supplies.append(unit)
            if self.is_fan(unit):
                fans.append(unit)
        if self.vendor_id and self.vendor_id == VENDOR_HP:
            # Index-numbers from HP-netboxes need to be re-numbered to match
            # index-numbers in POWERSUPPLY-MIB and FAN-MIB.
            # Index-numbers should in practice start at 1 for both PSUs and
            # FANs to match the corresponding statuses.
            power_supplies = self._rearrange_indexes(power_supplies)
            fans = self._rearrange_indexes(fans)
        # Create list of all psus and fans.  Add all psus first.
        all_psus_and_fans = power_supplies
        # Then add all fans.
        all_psus_and_fans.extend(fans)
        return all_psus_and_fans

    def is_fan(self, pwr):
        """Determine if this unit is a fan"""
        return (pwr.get('entPhysicalClass', None) == 'fan')

    def is_psu(self, pwr):
        """Determine if this unit is a powersupply"""
        return (pwr.get('entPhysicalClass', None) == 'powerSupply')

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
                self._logger.debug('PSU:FAN: %s' % psu_or_fan)
                entity_index = psu_or_fan.get(0, None)
                is_up = 'u'
                sensor_oid = None
                if self.entity_fru_control:
                    if self.is_fan(psu_or_fan):
                        # locate sensor and get status
                        ret = yield self.entity_fru_control.is_fan_up(
                                                                entity_index)
                        if ret:
                            is_up = ret
                            sensor_oid = (
                                self.entity_fru_control.get_oid_for_fan_status(
                                                                entity_index))
                        self._logger.debug('FAN: %s: %s' % (ret, sensor_oid))
                    elif self.is_psu(psu_or_fan):
                        ret = yield self.entity_fru_control.is_psu_up(
                                                                entity_index)
                        if ret:
                            is_up = ret
                            sensor_oid = (
                                self.entity_fru_control.get_oid_for_psu_status(
                                                                entity_index))
                        self._logger.debug('PSU: %s: %s' % (ret, sensor_oid))
                    phys_name = psu_or_fan.get('entPhysicalName', None)

                    power_supply = self.containers.factory(phys_name,
                                                    shadows.PowerSupplyOrFan)
                    # psu info
                    power_supply.netbox = self.netbox
                    power_supply.name = phys_name
                    power_supply.model = psu_or_fan.get('entPhysicalModelName',
                                                                        None)
                    power_supply.descr = psu_or_fan.get('entPhysicalDescr',
                                                                        None)
                    power_supply.physical_class = psu_or_fan.get(
                                                    'entPhysicalClass', None)
                    power_supply.sensor_oid = sensor_oid
                    power_supply.up = is_up
                    # device info
                    serial = psu_or_fan.get('entPhysicalSerialNum', None)
                    if serial:
                        device = self.containers.factory(serial,
                                                            shadows.Device)
                        device.serial = serial
                        device.hardware_version = psu_or_fan.get(
                                                'entPhysicalHardwareRev', None)
                        device.firmware_version = psu_or_fan.get(
                                                'entPhysicalFirmwareRev', None)
                        device.software_version = psu_or_fan.get(
                                                'entPhysicalSoftwareRev', None)
                        power_supply.device = device

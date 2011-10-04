# encoding: utf-8
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
"""ipdevpolld-plugin to collect redundant power-supply units and fans,- and
their correspnding status.

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

from nav.mibs.entity_mib import EntityMib

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
        if self.netbox.type:
            self.vendor_id = self.netbox.type.get_enterprise_id()
        if self.vendor_id == VENDOR_CISCO:
            self.entity_fru_control = CiscoEntityFruControlMib(self.agent)
        elif self.vendor_id == VENDOR_HP:
            self.entity_fru_control = HpEntityFruControlMib(self.agent)

    @classmethod
    def can_handle(cls, netbox):
        """Return always True"""
        return True

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

    def _get_redundant_psus_and_fans(self, to_filter):
        """ Filter out PSUs and FANs, and return only redundant."""
        power_supplies = []
        fans = []
        for unit in  to_filter.values():
            if self.is_psu(unit):
                power_supplies.append(unit)
            if self.is_fan(unit):
                fans.append(unit)
        filtered = []
        if self.vendor_id == VENDOR_HP:
            # Index-numbers from HP-netboxes need to be re-numbered to match
            # index-numbers in POWERSUPPLY-MIB and FAN-MIB.
            # Index-numbers should in practice start at 1 for both PSUs and
            # FANs to match the corresponding statuses.
            power_supplies = self._rearrange_indexes(power_supplies)
            fans = self._rearrange_indexes(fans)
        # Select only those boxes with more than one PSU
        if len(power_supplies) > 1:
            filtered = power_supplies
            filtered.extend(fans)
        return filtered

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
        entity_table = yield self.entity_mib.get_entity_physical_table()
        psus_and_fans = self._get_redundant_psus_and_fans(entity_table)
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
                power_supply = self.containers.factory(
                                    psu_or_fan.get('entPhysicalName', None),
                                                    shadows.PowerSupplyOrFan)
                # psu info
                power_supply.netbox = self.netbox
                power_supply.name = psu_or_fan.get('entPhysicalName', None)
                power_supply.model = psu_or_fan.get('entPhysicalModelName',
                                                                        None)
                power_supply.descr = psu_or_fan.get('entPhysicalDescr', None)
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

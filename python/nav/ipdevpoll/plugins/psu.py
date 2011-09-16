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
""" ipdevpolld plugin to collect redundant power-supply units.

This plugin uses ENTITY-MIB to retrieve all possible PSUs in network-
equipment.
"""
from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

from nav.mibs.entity_mib import EntityMib
from nav.mibs.entity_mib import EntityTable

class PowerSupplyUnit(Plugin):
    """Plugin that collect PSUs from netboxes."""

    def __init__(self, *args, **kwargs):
        super(PowerSupplyUnit, self).__init__(*args, **kwargs)
        self.entity_mib = EntityMib(self.agent)

    @classmethod
    def can_handle(cls, netbox):
        return True

    @defer.inlineCallbacks
    def get_physical_table(self):
        """ Get all entities in a netbox and return it as a table with
        dicts and table-index as key."""
        #self.entity_mib = EntityMib(self.agent)
        df = self.entity_mib.retrieve_table('entPhysicalTable')
        df.addCallback(self.entity_mib.translate_result)
        physical_table = yield df
        ent_table = EntityTable(physical_table)
        defer.returnValue(ent_table)

    def _get_powersupplies_and_fans(self, to_filter):
        """ Filter out """
        filtered = []
        for key, values in to_filter.items():
            if to_filter[key]['entPhysicalClass'] in ['powerSupply', 'fan']:
                filtered.append(values)
        return filtered

    @defer.inlineCallbacks
    def handle(self):
        self._logger.error("Collecting PSUs")
        entity_table = yield self.get_physical_table()
        pwrs_and_fans = self._get_powersupplies_and_fans(entity_table)
        redundant_pwrs = None
        if len(pwrs_and_fans) > 1:
            redundant_pwrs = pwrs_and_fans
        if redundant_pwrs:
            for pwr in redundant_pwrs:
                pwr_index = pwr.get(0, None)
                power_supply = self.containers.factory(pwr_index,
                                                        shadows.PowerSupply)
                # psu info
                power_supply.netbox = self.netbox
                power_supply.name = pwr.get('entPhysicalName', None)
                self._logger.error('%s: %s' % (self.netbox.sysname,
                                                    power_supply.name))
                power_supply.model = pwr.get('entPhysicalModelName', None)
                power_supply.descr = pwr.get('entPhysicalDescr', None)
                power_supply.physical_class = pwr.get('entPhysicalClass', None)
                power_supply.up = 'y'
                # device info
                serial = pwr.get('entPhysicalSerialNum', None)
                if serial:
                    device = self.containers.factory(pwr_index, shadows.Device)
                    device.serial = serial
                    device.hardware_version = pwr.get('entPhysicalHardwareRev',
                                                        None)
                    device.firmware_version = pwr.get('entPhysicalFirmwareRev',
                                                        None)
                    device.software_version = pwr.get('entPhysicalSoftwareRev',
                                                        None)
                    power_supply.device = device

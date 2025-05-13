#
# Copyright (C) 2009-2012 Uninett AS
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
"""ipdevpoll plugin to collect module information from ENTITY-MIB.

This will collect anything that looks like a field-replaceable module
with a serial number from the entPhysicalTable.  If a module has a
name that can be interpreted as a number, it will have its
module_number field set to this number.

entAliasMappingTable is collected; mappings between any physical
entity and an interface from IF-MIB is kept.  For each mapping found,
the interface will have its module set to be whatever the ancestor
module of the physical entity is.
"""

import configparser
import re

from twisted.internet import defer

from nav.mibs.entity_mib import EntityMib, EntityTable
from nav.ipdevpoll import Plugin, shadows
from nav.ipdevpoll.timestamps import TimestampChecker

INFO_VAR_NAME = 'modules'


class Modules(Plugin):
    """Plugin to collect module data from devices"""

    def __init__(self, *args, **kwargs):
        super(Modules, self).__init__(*args, **kwargs)
        self.alias_mapping = {}
        self.entitymib = EntityMib(self.agent)
        self.stampcheck = TimestampChecker(self.agent, self.containers, INFO_VAR_NAME)

    @classmethod
    def on_plugin_load(cls):
        from nav.ipdevpoll.config import ipdevpoll_conf

        cls.ignored_serials = get_ignored_serials(ipdevpoll_conf)

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("Collecting ENTITY-MIB module data")
        need_to_collect = yield self._need_to_collect()
        if need_to_collect:
            physical_table = yield self.entitymib.get_entity_physical_table()

            self.alias_mapping = yield self.entitymib.get_alias_mapping()
            self._process_entities(physical_table)
        self.stampcheck.save()

    @defer.inlineCallbacks
    def _need_to_collect(self):
        yield self.stampcheck.load()
        yield self.stampcheck.collect([self.entitymib.get_last_change_time()])

        result = yield self.stampcheck.is_changed()
        return result

    def _device_from_entity(self, ent):
        serial_column = 'entPhysicalSerialNum'
        if serial_column in ent and ent[serial_column] and ent[serial_column].strip():
            serial_number = ent[serial_column].strip()
            device_key = serial_number
        else:
            serial_number = None
            device_key = 'unknown-%s' % ent[0]

        if serial_number in self.ignored_serials:
            self._logger.debug("ignoring %r due to ignored serial number", ent)
            return None

        device = self.containers.factory(device_key, shadows.Device)
        if serial_number:
            device.serial = serial_number
        if ent['entPhysicalHardwareRev']:
            device.hardware_version = ent['entPhysicalHardwareRev'].strip()
        if ent['entPhysicalSoftwareRev']:
            device.software_version = ent['entPhysicalSoftwareRev'].strip()
        if ent['entPhysicalFirmwareRev']:
            device.firmware_version = ent['entPhysicalFirmwareRev'].strip()
        device.active = True
        return device

    def _module_from_entity(self, ent):
        module = self.containers.factory(ent['entPhysicalSerialNum'], shadows.Module)
        netbox = self.containers.factory(None, shadows.Netbox)

        module.netbox = netbox
        module.model = ent['entPhysicalModelName'].strip()
        module.description = ent['entPhysicalDescr'].strip()
        module.name = ent['entPhysicalName'].strip()
        if module.name.strip().isdigit():
            module.module_number = int(module.name.strip())
        module.parent = None
        return module

    def _process_modules(self, entities):
        # map entity indexes to module containers
        module_containers = {}
        modules = entities.get_modules()
        for ent in modules:
            entity_index = ent[0]
            device = self._device_from_entity(ent)
            if not device:
                continue  # this device was ignored
            module = self._module_from_entity(ent)
            module.device = device

            module_containers[entity_index] = module
            self._logger.debug("module (entPhysIndex=%s): %r", entity_index, module)

        return module_containers

    def _process_ports(self, entities, module_containers):
        ports = entities.get_ports()
        netbox = self.containers.factory(None, shadows.Netbox)

        # Map interfaces to modules, if possible
        module_ifindex_map = {}  # just for logging debug info
        for port in ports:
            entity_index = port[0]
            if entity_index in self.alias_mapping:
                module_entity = entities.get_nearest_module_parent(port)

                if module_entity and module_entity[0] in module_containers:
                    module = module_containers[module_entity[0]]
                    indices = self.alias_mapping[entity_index]
                    for ifindex in indices:
                        interface = self.containers.factory(ifindex, shadows.Interface)
                        interface.netbox = netbox
                        interface.ifindex = ifindex
                        interface.module = module

                        if module.name in module_ifindex_map:
                            module_ifindex_map[module.name].append(ifindex)
                        else:
                            module_ifindex_map[module.name] = [ifindex]

        if module_ifindex_map:
            self._logger.debug("module/ifindex mapping: %r", module_ifindex_map)

    def _process_entities(self, result):
        """Process the list of collected entities."""
        # be able to look up all entities using entPhysicalIndex
        entities = EntityTable(result)

        module_containers = self._process_modules(entities)
        self._process_ports(entities, module_containers)


def get_ignored_serials(config: configparser.ConfigParser) -> list[str]:
    """Returns a list of ignored serial numbers from a ConfigParser instance"""
    if config is None:
        return []

    raw_string = config.get("modules", "ignored-serials", fallback="BUILTIN")
    values = re.split(r" +", raw_string)
    return [v for v in values if v]

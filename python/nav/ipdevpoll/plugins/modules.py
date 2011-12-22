#
# Copyright (C) 2009-2011 UNINETT AS
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
"""ipdevpoll plugin to collect chassis and module information from ENTITY-MIB.

This will collect anything that looks like a field-replaceable module
with a serial number from the entPhysicalTable.  If a module has a
name that can be interpreted as a number, it will have its
module_number field set to this number.

The chassis device will have its serial number and hw/sw/fw-version
set from the same MIB.

entAliasMappingTable is collected; mappings between any physical
entity and an interface from IF-MIB is kept.  For each mapping found,
the interface will have its module set to be whatever the ancestor
module of the physical entity is.
"""

from twisted.internet import defer

from nav.oids import OID
from nav.mibs.entity_mib import EntityMib, EntityTable
from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

class Modules(Plugin):
    """Plugin to collect module and chassis data from devices"""

    @classmethod
    def can_handle(cls, netbox):
        return True

    def __init__(self, *args, **kwargs):
        super(Modules, self).__init__(*args, **kwargs)
        self.alias_mapping = {}

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("Collecting ENTITY-MIB module data")
        entitymib = EntityMib(self.agent)

        df = entitymib.retrieve_table('entPhysicalTable')
        df.addCallback(entitymib.translate_result)
        physical_table = yield df

        alias_mapping = yield entitymib.retrieve_column(
            'entAliasMappingIdentifier')
        self.alias_mapping = self._process_alias_mapping(alias_mapping)
        self._process_entities(physical_table)


    def _device_from_entity(self, ent, chassis=False):
        serial_column = 'entPhysicalSerialNum'
        if serial_column in ent and ent[serial_column] and \
            ent[serial_column].strip():
            serial_number = ent[serial_column].strip()
            device_key = serial_number
        else:
            serial_number = None
            device_key = 'unknown-%s' % ent[0]

        # check whether some plugin already registered a chassis device
        # without knowing its serial. If so, give the device two keys in the
        # container repository
        if chassis and self.containers.get(None, shadows.Device):
            device = self.containers.get(None, shadows.Device)
            self.containers[shadows.Device][device_key] = device
        else:
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
        module = self.containers.factory(ent['entPhysicalSerialNum'],
                                         shadows.Module)
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
            module = self._module_from_entity(ent)
            module.device = device

            module_containers[entity_index] = module
            self._logger.debug("module (entPhysIndex=%s): %r",
                               entity_index, module)

        return module_containers

    def _process_chassis(self, entities):
        chassis = entities.get_chassis()
        if not chassis:
            self._logger.debug('No chassis found')
            return
        elif len(chassis) > 1:
            self._logger.debug('Found multiple chassis')

        # We don't really know how to handle a multiple chassis
        # situation.  Best effort is to use the first one in the list.
        # This should be revised by someone who has stacked chassis
        # devices to test on.
        the_chassis = chassis[0]
        device = self._device_from_entity(the_chassis, chassis=True)
        netbox = self.containers.factory(None, shadows.Netbox)
        netbox.device = device

    def _process_ports(self, entities, module_containers):
        ports = entities.get_ports()
        netbox = self.containers.factory(None, shadows.Netbox)

        # Map interfaces to modules, if possible
        module_ifindex_map = {} #just for logging debug info
        for port in ports:
            entity_index = port[0]
            if entity_index in self.alias_mapping:
                module_entity = entities.get_nearest_module_parent(port)

                if module_entity and module_entity[0] in module_containers:
                    module = module_containers[ module_entity[0] ]
                    indices = self.alias_mapping[entity_index]
                    for ifindex in indices:
                        interface = self.containers.factory(ifindex,
                                                            shadows.Interface)
                        interface.netbox = netbox
                        interface.ifindex = ifindex
                        interface.module = module

                        if module.name in module_ifindex_map:
                            module_ifindex_map[module.name].append(ifindex)
                        else:
                            module_ifindex_map[module.name] = [ifindex]

        if module_ifindex_map:
            self._logger.debug("module/ifindex mapping: %r",
                              module_ifindex_map)


    def _process_entities(self, result):
        """Process the list of collected entities."""
        # be able to look up all entities using entPhysicalIndex
        entities = EntityTable(result)

        module_containers = self._process_modules(entities)
        self._process_chassis(entities)
        self._process_ports(entities, module_containers)


    def _process_alias_mapping(self, alias_mapping):
        mapping = {}
        for (phys_index, _logical), rowpointer in alias_mapping.items():
            # Last element is ifindex. Preceding elements is an OID.
            ifindex = OID(rowpointer)[-1]

            if phys_index not in mapping:
                mapping[phys_index] = []
            mapping[phys_index].append(ifindex)

        self._logger.debug("alias mapping: %r", mapping)
        return mapping



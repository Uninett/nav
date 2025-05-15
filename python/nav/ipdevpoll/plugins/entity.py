#
# Copyright (C) 2009-2012, 2015 Uninett AS
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
"""
ipdevpoll plugin to collect information about physical entities, if any,
within a Netbox, from the ENTITY-MIB::entPhysicalTable (RFC 4133 and RFC 6933)
"""

from twisted.internet import defer

from nav.Snmp import safestring
from nav.ipdevpoll.shadows.entity import NetboxEntity

from nav.mibs.entity_mib import EntityMib, EntityTable
from nav.ipdevpoll import Plugin, shadows
from nav.ipdevpoll.plugins.modules import get_ignored_serials
from nav.ipdevpoll.timestamps import TimestampChecker
from nav.models import manage

INFO_VAR_NAME = 'entityphysical'


class Entity(Plugin):
    """Plugin to collect physical entity data from devices"""

    def __init__(self, *args, **kwargs):
        super(Entity, self).__init__(*args, **kwargs)
        self.alias_mapping = {}
        self.entitymib = EntityMib(self.agent)
        self.stampcheck = TimestampChecker(self.agent, self.containers, INFO_VAR_NAME)

    @classmethod
    def on_plugin_load(cls):
        from nav.ipdevpoll.config import ipdevpoll_conf

        cls.ignored_serials = get_ignored_serials(ipdevpoll_conf)

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("Collecting physical entity data")
        # Temporarily disabled due to consistency issues with some vendors:
        # need_to_collect = yield self._need_to_collect()
        # if need_to_collect:
        if True:
            physical_table = yield self.entitymib.get_entity_physical_table()
            self._logger.debug("found %d entities", len(physical_table))
            self._process_entities(physical_table)
        self.stampcheck.save()

    @defer.inlineCallbacks
    def _need_to_collect(self):
        yield self.stampcheck.load()
        yield self.stampcheck.collect([self.entitymib.get_last_change_time()])

        result = yield self.stampcheck.is_changed()
        return result

    def _process_entities(self, result):
        """Process the list of collected entities."""
        # be able to look up all entities using entPhysicalIndex
        entities = EntityTable(result)
        containers = [
            self._container_from_entity(entity)
            for _, entity in sorted(entities.items())
        ]
        self._fix_hierarchy(containers)

    def _fix_hierarchy(self, containers):
        by_index = {c.index: c for c in containers}
        ghosts = set()
        for container in containers:
            if container.contained_in:
                parent_id = str(container.contained_in)
                parent = by_index.get(parent_id)
                if parent:
                    container.contained_in = parent
                else:
                    ghosts.add(str(container.contained_in))
                    container.contained_in = None

        if ghosts:
            self._logger.info(
                "kick your device vendor in the shin. entPhysicalContainedIn "
                "values refer to non-existant entities: %s",
                ", ".join(ghosts),
            )

    field_map = {
        k: 'entPhysical' + v
        for k, v in dict(
            index='Index',
            descr='Descr',
            vendor_type='VendorType',
            contained_in='ContainedIn',
            physical_class='Class',
            parent_relpos='ParentRelPos',
            name='Name',
            hardware_revision='HardwareRev',
            firmware_revision='FirmwareRev',
            software_revision='SoftwareRev',
            mfg_name='MfgName',
            model_name='ModelName',
            alias='Alias',
            asset_id='AssetID',
            fru='IsFRU',
            mfg_date='MfgDate',
            uris='Uris',
            serial='SerialNum',
        ).items()
    }

    class_map = {name: value for value, name in manage.NetboxEntity.CLASS_CHOICES}

    def _container_from_entity(self, ent):
        device_key = 'ENTITY-MIB:' + str(ent.get(0))

        container = self.containers.factory(device_key, NetboxEntity)
        netbox = self.containers.factory(None, shadows.Netbox)
        container.netbox = netbox
        container.index = ent.get(0)
        container.source = 'ENTITY-MIB'

        for attr, column in self.field_map.items():
            value = ent.get(column)
            if column in EntityMib.text_columns and value and "\x00" in value:
                value = value.replace("\x00", "")  # Remove broken stuff from text
            if column in ("entPhysicalVendorType", "entPhysicalUris") and value:
                value = safestring(value).replace("\x00", "")
            if column == 'entPhysicalClass':
                value = self.class_map.get(value)
            if value is not None:
                setattr(container, attr, value)

        serial_num = getattr(container, 'serial', None)
        if serial_num and serial_num not in self.ignored_serials:
            device = self.containers.factory(container.serial, shadows.Device)
            device.serial = serial_num
            for key in ('hardware', 'firmware', 'software'):
                val = getattr(container, key + '_revision')
                if val:
                    version = getattr(device, key + '_version', None)
                    if not version:
                        setattr(device, key + '_version', val)
            device.active = True
            container.device = device

        return container

# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
"""ipdevpoll plugin to collect module information from ENTITY-MIB.

"""

import logging
import pprint
from datetime import datetime

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.mibs.entity_mib import EntityMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage
from nav.models import manage

class Modules(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def __init__(self, *args, **kwargs):
        super(Modules, self).__init__(*args, **kwargs)
        self.alias_mapping = {}

    @defer.deferredGenerator
    def handle(self):
        self.logger.debug("Collecting ENTITY-MIB module data")
        entitymib = EntityMib(self.job_handler.agent)
        dw = defer.waitForDeferred(entitymib.retrieve_table('entPhysicalTable'))
        yield dw
        physical_table = entitymib.translate_result(dw.getResult())

        dw = defer.waitForDeferred(entitymib.retrieve_column('entAliasMappingIdentifier'))
        yield dw
        alias_mapping = dw.getResult()

        for (phys_index, logical), row in alias_mapping.items():
            # Last element is ifindex. Preceeding elements is an OID.
            ifindex = row.pop()

            if phys_index not in self.alias_mapping:
                self.alias_mapping[phys_index] = []
            self.alias_mapping[phys_index].append(ifindex)

        print self.alias_mapping
        self._process_entities(physical_table)

    def _error(self, failure):
        """Errback for SNMP failures."""
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)

    def _process_entities(self, result):
        """Process the list of collected entities."""

        modules = self._filter_modules(result)
        netbox = self.job_handler.container_factory(storage.Netbox, key=None)

        for ent in modules:
            device = self.job_handler.container_factory(
                storage.Device, key=ent['entPhysicalSerialNum'])
            device.serial = ent['entPhysicalSerialNum']
            device.hardware_version = ent['entPhysicalHardwareRev']
            device.software_version = ent['entPhysicalSoftwareRev']
            device.firmware_version = ent['entPhysicalFirmwareRev']
            device.auto = True
            device.active = True
            device.discovered = datetime.now()

            module = self.job_handler.container_factory(
                storage.Module, key=(netbox, ent['entPhysicalName']))
            module.device = device
            module.netbox = netbox
            module.module_number = ent.index[0]
            module.model = ent['entPhysicalModelName']
            module.description = ent['entPhysicalDescr']
            module.up = "y"
            module.name = ent['entPhysicalName']
            module.parent = ent['entPhysicalContainedIn']

            if ent.index[0] in self.alias_mapping:
                indices = self.alias_mapping[ent.index[0]]
                for ifindex in indices:
                    interface = self.job_handler.container_factory(
                        storage.Interface, key=(netbox, ifindex))
                    interface.netbox = netbox
                    interface.ifindex = ifindex
                    interface.module = module
                    interface.update_only = True

    def _filter_modules(self, entities):
        """Filter out anything but field replaceable modules with
        serial numbers.

        """
        def is_module(e):
            return e['entPhysicalClass'] == 'module' and \
                e['entPhysicalIsFRU'] and \
                e['entPhysicalSerialNum']

        modules = [entity for entity in entities.values()
                   if is_module(entity)]
        return modules

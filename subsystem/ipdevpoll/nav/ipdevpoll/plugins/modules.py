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

    def handle(self):
        self.logger.debug("Collecting ENTITY-MIB module data")
        self.entitymib = EntityMib(self.job_handler.agent)
        df = self.entitymib.retrieve_table('entPhysicalTable')
        df.addCallback(self.entitymib.translate_result)
        df.addCallback(self._process_entities)
        df.addErrback(self._error)
        return df

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

        #self.logger.debug(pprint.pformat(result))
        modules = self._filter_modules(result)
        self.logger.debug(pprint.pformat(modules))


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

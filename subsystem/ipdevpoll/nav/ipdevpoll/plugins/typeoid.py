# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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
"""ipdevpoll type detection plugin.

Collects sysObjectId and compares with the registered type of the
netbox.

TODO: If netbox type has changed, NAVdb needs to be updated, an event
      must be dispatched, and the poll run restarted.

"""

import logging
import pprint

from twisted.internet import defer, threads
from twisted.python.failure import Failure

from nav.ipdevpoll import Plugin, storage, shadows
from nav.ipdevpoll.models import Type, OID
from nav.mibs.snmpv2_mib import Snmpv2Mib
from nav.models import manage

class InvalidResponseError(Exception):
    pass

class TypeOid(Plugin):
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.deferred = defer.Deferred()

    def __cmp__(self, other):
        # Always sort the TypeOid plugin first
        return -1

    @classmethod
    def can_handle(self, netbox):
        return True

    @defer.deferredGenerator
    def handle(self):
        self.logger.debug("Collecting sysObjectId")
        snmpv2_mib = Snmpv2Mib(self.agent)
        thing = defer.waitForDeferred(
            snmpv2_mib.get_sysObjectID())
        yield thing

        thing = thing.getResult()
        if not thing:
            raise InvalidResponseError("No response on sysObjectID query.", 
                                       thing, self.agent)
        # Just pick the first result, there should never really be multiple
        sysobjectid = str( OID(thing) )
        # ObjectIDs in the database are stored without the preceding dot.
        if sysobjectid[0] == '.':
            sysobjectid = sysobjectid[1:]

        
        self.logger.debug("sysObjectID is %s", sysobjectid)
        if self.netbox.type is None or \
                self.netbox.type.sysobjectid != str(sysobjectid):
            self.logger.warning("Netbox has changed type from %r",
                                self.netbox.type)

        # Look up existing type
        types = manage.NetboxType.objects.filter(sysobjectid=str(sysobjectid))
        thing = defer.waitForDeferred(
            threads.deferToThread(storage.shadowify_queryset_and_commit,
                                  types))
        yield thing
        types = thing.getResult()

        # Set the found type
        if not types:
            self.logger.warn("sysObjectID %r is unknown to NAV", sysobjectid)
        else:
            type_ = types[0]
            netbox_container = self.containers.factory(None, shadows.Netbox)
            netbox_container.type = type_
        yield True


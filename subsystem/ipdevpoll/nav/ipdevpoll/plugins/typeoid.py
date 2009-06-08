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

from twisted.internet import defer
from twisted.python.failure import Failure

from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll.models import Type, OID
from nav.mibs import Snmpv2Mib

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

    def handle(self):
        self.logger.debug("Collecting sysObjectId")
        snmpv2_mib = Snmpv2Mib(self.job_handler.agent)
        df = snmpv2_mib.get_sysObjectID()
        df.addCallback(self.get_results)
        df.addErrback(self.error)
        return self.deferred

    def error(self, failure):
        failure.trap(defer.TimeoutError)
        # Handle TimeoutErrors
        self.logger.error(failure.getErrorMessage())
        # Report this failure to the waiting plugin manager (RunHandler)
        exc = FatalPluginError("Cannot continue due to device timeouts")
        failure = Failure(exc)
        self.deferred.errback(failure)

    def get_results(self, result):
        sysobjectid = result
        self.logger.debug("sysObjectID is %s" % sysobjectid)
        if self.netbox.type.sysobjectid != sysobjectid:
                self.logger.warning("Netbox has changed type from %r",
                                    self.netbox.type)
        
        self.deferred.callback(True)
        return result

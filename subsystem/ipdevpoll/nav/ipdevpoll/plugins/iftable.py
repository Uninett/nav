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
"""ipdevpoll plugin to pull iftable date.

Just a prototype, will only log info, not store it in NAVdb.

"""

import logging
import pprint

from pysnmp.asn1.oid import OID

from twisted.internet import defer
from twisted.python.failure import Failure

from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll.plugins import register

class Interfaces(Plugin):
    def __init__(self, netbox):
        Plugin.__init__(self, netbox)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        return netbox.is_supported_oid("ifDescr")

    def handle(self):
        self.logger.debug("Collecting ifDescr")
        df = self.netbox.get_table("ifDescr")
        df.addCallback(self.got_results)
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

    def got_results(self, result):
        ifdescrs = result.values()[0]
        self.logger.debug("Found %d interfaces", len(ifdescrs))
        #self.logger.debug('Results: %s', pprint.pformat(result))
        self.deferred.callback(True)
        return result

register(Interfaces)

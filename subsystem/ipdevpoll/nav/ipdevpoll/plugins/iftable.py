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

from twisted.internet import defer
from twisted.python.failure import Failure

from nav.mibs import IfMib
from nav.ipdevpoll import Plugin, FatalPluginError

class Interfaces(Plugin):
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self.logger.debug("Collecting ifTable columns")
        self.ifmib = IfMib(self.netbox.get_proxy())
        df = self.ifmib.retrieve_table_columns('ifTable',
            ['ifDescr',
             'ifType',
             'ifSpeed',
             'ifPhysAddress',
             'ifAdminStatus',
             'ifOperStatus',
             ])
        df.addCallback(self.got_iftable)
        df.addErrback(self.error)
        return self.deferred

    def error(self, failure):
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)

    def got_iftable(self, result):
        self.iftable = result
        self.logger.debug("Found %d interfaces", len(result))
        #self.logger.debug('Results: %s', pprint.pformat(result))
        self.logger.debug("Collecting ifXTable columns")
        df = self.ifmib.retrieve_table_columns('ifXTable',
            ['ifName',
             'ifHighSpeed',
             'ifConnectorPresent',
             'ifAlias',
             ])
        df.addCallback(self.got_ifxtable)
        df.addErrback(self.error)
        return result

    def got_ifxtable(self, result):
        for key in result.keys():
            if key in self.iftable:
                self.iftable[key].update(result[key])
            else:
                self.iftable[key] = result.key()

        self.logger.debug('Full table: %s', pprint.pformat(self.iftable))
        # Now save stuff to containers and signal our exit
        self.deferred.callback(True)
        return result


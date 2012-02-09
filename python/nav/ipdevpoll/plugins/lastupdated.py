#
# Copyright (C) 2010, 2011 UNINETT AS
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
"""ipdevpoll netbox lastUpdated timestamp updater plugin."""

from twisted.internet import defer, reactor

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
import time

class LastUpdated(Plugin):
    def handle(self):
        self._logger.debug("Updating lastupdated timestamp")

        # Convention is to store timestamp as milliseconds since the epoch in
        # the NetboxInfo table
        timestamp = long(time.time() * 1000)

        var_name = 'lastUpdated'
        netbox = self.containers.factory(None, shadows.Netbox)
        info = self.containers.factory(var_name, shadows.NetboxInfo)
        info.netbox = netbox
        info.key = None
        info.variable = var_name
        info.value = str(timestamp)

        # We don't do any I/O, but need to return a deferred.
        # TODO: Maybe calls to plugins should be wrapped in a
        # defer.maybeDeferred
        d = defer.Deferred()
        reactor.callLater(0, d.callback, True)
        return d


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
"""ipdevpoll plugin to collect bridge data.

This plugin doesn't do much except find baseport numbers for switch
ports, using the BRIDGE-MIB.

TODO: This version of the plugin will not support multiple BRIDGE-MIB
entities, such as on Cisco switches. A future version must be updated
to poll all BRIDGE-MIB instances mentioned in
ENTITY-MIB::entLogicalTable.

"""

from twisted.internet import defer
from twisted.python.failure import Failure

from nav.mibs.bridge_mib import BridgeMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage

class Bridge(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        return True

    def handle(self):
        self.logger.debug("Collecting bridge data")
        self.bridge = BridgeMib(self.job_handler.agent)
        df = self.bridge.retrieve_column('dot1dBasePortIfIndex')
        df.addCallback(self._set_port_numbers)
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
        return failure

    def _set_port_numbers(self, result):
        """Process the list of collected base ports and set port numbers."""

        self.logger.debug("Found %d base (switch) ports: %r", 
                          len(result),
                          [portnum[0] for portnum in result.keys()])

        # Now save stuff to containers and pass the list of containers
        # to the next callback
        for portnum, ifindex in result.items():
            # The index is a single integer
            portnum = portnum[0]
            interface = self.job_handler.container_factory(storage.Interface, 
                                                           key=ifindex)
            interface.baseport = portnum

        return result
    

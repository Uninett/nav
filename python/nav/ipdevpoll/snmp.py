#
# Copyright (C) 2011 UNINETT AS
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
"""selects and provides SNMP backend for ipdevpoll"""

import sys
import socket
import logging

from twisted.internet import defer, reactor
from twisted.python.failure import Failure

try:
    import pynetsnmp.twistedsnmp
    from pynetsnmp.twistedsnmp import snmpprotocol
except ImportError:
    from twistedsnmp import snmpprotocol, agentproxy

    import warnings
    warnings.warn("Using pure Python-based SNMP library, which will affect "
                  "performance")

    class AgentProxy(agentproxy.AgentProxy):
        """TwistedSNMP AgentProxy derivative to add API compatibility
        with pynetsnmp's AgentProxy's open/close methods.

        """
        def open(self):
            """Dummy open method"""
            pass

        def close(self):
            """Dummy close method"""
            pass

        def walk(self, oid, timeout=2.0, retry_count=4):
            """Our own low-level implementation of a GET-NEXT operation for a
            twistedsnmp AgentProxy, since it doesn't provide its own.

            """
            oids = [oid]
            try:
                request = self.encode(oids, self.community, next=True)
                key = self.getRequestKey(request)
                self.send(request.encode())
            except socket.error:
                return defer.fail(Failure())

            def _as_dictionary(value):
                try:
                    return dict(value)
                except Exception:
                    logger = logging.getLogger(__name__)
                    logger.exception(
                        "Failure converting query results %r to dictionary",
                        value)
                    return {}

            df = defer.Deferred()
            df.addCallback(self.getResponseResults)
            df.addCallback(_as_dictionary)
            timer = reactor.callLater(timeout, self._timeout,
                                      key, df, oids, timeout, retry_count)
            self.protocol.requests[key] = df, timer
            return df

else:
    class AgentProxy(pynetsnmp.twistedsnmp.AgentProxy):
        """pynetsnmp AgentProxy derivative to adjust the silly 1000 value
        limit imposed in getTable calls"""

        def getTable(self, *args, **kwargs):
            if 'limit' not in kwargs:
                kwargs['limit'] = sys.maxint
            return pynetsnmp.twistedsnmp.AgentProxy.getTable(self,
                                                             *args, **kwargs)

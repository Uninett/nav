#
# Copyright (C) 2011,2012 UNINETT AS
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
"""twistedsnmp compatibility"""
# pylint: disable=E1101,W0611,W0703

from __future__ import absolute_import
import socket
import logging

from twisted.internet import defer, reactor
from twisted.python.failure import Failure
from twistedsnmp import snmpprotocol, agentproxy

from . import common

class AgentProxy(common.AgentProxyMixIn, agentproxy.AgentProxy):
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


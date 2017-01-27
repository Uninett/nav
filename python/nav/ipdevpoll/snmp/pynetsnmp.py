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
"""pynetsnmp compatibility"""
# pylint: disable=C0103,C0111,W0703,R0903,W0611

from __future__ import absolute_import
from IPy import IP
import sys
import inspect

from pynetsnmp import twistedsnmp, netsnmp, version
from pynetsnmp.twistedsnmp import snmpprotocol

from . import common


def pynetsnmp_limits_results():
    """Returns True if the available pynetsnmp version limits the number of
    results of getTable operations.

    ipdevpoll doesn't want this arbitrary limit, which appeared sometime
    between pynetsnmp 0.28.8 and 0.28.14.

    """
    try:
        from pynetsnmp.tableretriever import TableRetriever
    except ImportError:
        return False
    else:
        args = inspect.getargspec(TableRetriever.__init__)[0]
        return 'limit' in args


def pynetsnmp_supports_ipv6():
    """
    Returns True if the available pynetsnmp version is known to support
    IPv6 addresses without modification
    """
    ver = [int(i) for i in version.VERSION.split('.')]
    return ver >= [0, 29, 2]


class AgentProxy(common.AgentProxyMixIn, twistedsnmp.AgentProxy):
    """pynetsnmp AgentProxy derivative to adjust the silly 1000 value
    limit imposed in getTable calls"""

    def __init__(self, *args, **kwargs):
        super(AgentProxy, self).__init__(*args, **kwargs)
        self._ipv6_check()

    if pynetsnmp_supports_ipv6():
        def _ipv6_check(self):
            pass
    else:
        def _ipv6_check(self):
            try:
                address = IP(self.ip)
            except ValueError:
                return
            if address.version() == 6:
                self.ip = 'udp6:[%s]' % self.ip

    if pynetsnmp_limits_results():
        def getTable(self, *args, **kwargs):
            if 'limit' not in kwargs:
                kwargs['limit'] = sys.maxint
            return super(AgentProxy, self).getTable(*args, **kwargs)

    def open(self):
        try:
            super(AgentProxy, self).open()
        except netsnmp.SnmpError, error:
            raise common.SnmpError(
                "could not open session for %s:%s, maybe too many open file "
                "descriptors?" % (self.ip, self.port))

    @classmethod
    def count_open_sessions(cls):
        "Returns a count of the number of open SNMP sessions in this process"
        import gc
        mykind = (o for o in gc.get_objects() if isinstance(o, cls))
        open_sessions = [o for o in mykind if getattr(o.session, 'sess', None)]
        return len(open_sessions)

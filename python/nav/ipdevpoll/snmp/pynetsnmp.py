#
# Copyright (C) 2011,2012 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""pynetsnmp compatibility"""

import inspect
import os

import sys

# don't have NET-SNMP load and parse MIB modules, we don't use them
# and we don't need all the parsing errors in our logs
os.environ['MIBS'] = ''
os.environ['MIBDIRS'] = ''

from pynetsnmp import twistedsnmp, netsnmp
from pynetsnmp.twistedsnmp import snmpprotocol

from . import common

__all__ = ["snmpprotocol", "pynetsnmp_limits_results", "AgentProxy"]


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
        args = inspect.getfullargspec(TableRetriever.__init__)[0]
        return 'limit' in args


class AgentProxy(common.AgentProxyMixIn, twistedsnmp.AgentProxy):
    """pynetsnmp AgentProxy derivative to adjust the silly 1000 value
    limit imposed in getTable calls"""

    if pynetsnmp_limits_results():

        def getTable(self, *args, **kwargs):
            if 'limit' not in kwargs:
                kwargs['limit'] = sys.maxsize
            return super(AgentProxy, self).getTable(*args, **kwargs)

    def open(self):
        try:
            super(AgentProxy, self).open()
        except netsnmp.SnmpError:
            raise common.SnmpError(
                "could not open session for %s:%s, maybe too many open file "
                "descriptors?" % (self.ip, self.port)
            )

    @classmethod
    def count_open_sessions(cls):
        "Returns a count of the number of open SNMP sessions in this process"
        import gc

        mykind = (o for o in gc.get_objects() if isinstance(o, cls))
        open_sessions = [o for o in mykind if getattr(o.session, 'sess', None)]
        return len(open_sessions)

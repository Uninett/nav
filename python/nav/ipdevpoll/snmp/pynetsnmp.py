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
"""pynetsnmp compatibility"""
# pylint: disable=C0103,C0111,W0703,R0903,W0611

from __future__ import absolute_import
import sys
import inspect

from pynetsnmp import twistedsnmp
from pynetsnmp.twistedsnmp import snmpprotocol

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

class AgentProxy(twistedsnmp.AgentProxy):
    """pynetsnmp AgentProxy derivative to adjust the silly 1000 value
    limit imposed in getTable calls"""

    if pynetsnmp_limits_results():
        def getTable(self, *args, **kwargs):
            if 'limit' not in kwargs:
                kwargs['limit'] = sys.maxint
            return twistedsnmp.AgentProxy.getTable(self, *args, **kwargs)

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

from pynetsnmp import twistedsnmp
from pynetsnmp.twistedsnmp import snmpprotocol

class AgentProxy(twistedsnmp.AgentProxy):
    """pynetsnmp AgentProxy derivative to adjust the silly 1000 value
    limit imposed in getTable calls"""

    def getTable(self, *args, **kwargs):
        if 'limit' not in kwargs:
            kwargs['limit'] = sys.maxint
        return twistedsnmp.AgentProxy.getTable(self, *args, **kwargs)

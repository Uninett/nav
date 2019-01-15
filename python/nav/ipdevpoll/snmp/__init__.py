#
# Copyright (C) 2011 Uninett AS
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
"""selects a proper SNMP backend for ipdevpoll"""

from __future__ import absolute_import

try:
    import pynetsnmp.twistedsnmp
except ImportError:
    raise ImportError("No supported SNMP backend was found")
else:
    from nav.ipdevpoll.snmp.pynetsnmp import AgentProxy, snmpprotocol

from .common import SnmpError

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
"""selects a proper SNMP backend for ipdevpoll"""

from __future__ import absolute_import
import warnings

try:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import pynetsnmp.twistedsnmp
except ImportError:
    from nav.ipdevpoll.snmp.twistedsnmp import AgentProxy, snmpprotocol
    warnings.warn("Using pure Python-based SNMP library, which will affect "
                  "performance")
else:
    from nav.ipdevpoll.snmp.pynetsnmp import AgentProxy, snmpprotocol
finally:
    warnings.resetwarnings()

from .common import SnmpError

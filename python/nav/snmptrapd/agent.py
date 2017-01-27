#
# Copyright (C) 2010, 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Trap manager functionality for snmptrapd."""
import logging
from nav.Snmp import BACKEND

if BACKEND == 'v2':
    from .agent_v2 import *
elif BACKEND == 'se':
    from .agent_se import *
elif BACKEND == 'pynetsnmp':
    from .agent_pynetsnmp import *
else:
    raise ImportError("No supported SNMP backend was found")

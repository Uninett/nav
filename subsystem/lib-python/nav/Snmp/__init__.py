#
# Copyright (C) 2010 UNINETT AS
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
"""A high level interface to SNMP query functionality for NAV, as pysnmp is
quite low-level and tedious to work with.

This interface supports both PySNMP v2 and PySNMP SE.
"""
import pysnmp

# Set default backend
backend = 'v2'
try:
    from pysnmp import version
    version.verifyVersionRequirement(3, 4, 3)
    backend = 'se'
except ImportError, e:
    pass

if backend == 'v2':
    from pysnmp_v2 import *
elif backend == 'se':
    from pysnmp_se import *

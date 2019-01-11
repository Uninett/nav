#
# Copyright (C) 2010, 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A high level interface for synchronouse SNMP operations in NAV.

This interface only supports pynetsnmp, but is designed to allow
multiple implementations

"""
from __future__ import absolute_import

BACKEND = None

try:
    # our highest preference is pynetsnmp, since it can support IPv6
    import pynetsnmp
except ImportError:
    pass
else:
    BACKEND = 'pynetsnmp'

# These wildcard imports are informed, not just accidents.
# pylint: disable=W0401
if BACKEND == 'pynetsnmp':
    from .pynetsnmp import *
else:
    raise ImportError("No supported SNMP backend was found")

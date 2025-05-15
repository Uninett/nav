# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-20011, 2015 Uninett AS
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
"""
A class that tries to retrieve all sensors from Geist-branded WeatherGoose
products.

Uses the vendor-specific GEIST-MIB-V3 (derived from the IT-WATCHDOGS-MIB-V3)
to detect and collect sensor-information.

"""

from nav.oids import OID
from nav.smidumps import get_mib
from .itw_mibv3 import ItWatchDogsMibV3


class GeistMibV3(ItWatchDogsMibV3):
    """
    A MibRetriever for retrieving information from Geist branded
    WeatherGoose products.

    Based on the GEIST-MIB-V3, which is more or less derived from the
    IT-WATCHDOGS-MIB-V3. Objects names in the derived MIB are mostly the
    same, except for a `cm` prefix on notification objects, which has changed
    to the `gst` prefix. This implementation does not use the notification
    objects for anything, so we don't need to care about this name change here.

    """

    mib = get_mib('GEIST-MIB-V3')

    oid_name_map = {OID(attrs['oid']): name for name, attrs in mib['nodes'].items()}

    lowercase_nodes = {key.lower(): key for key in mib['nodes']}

# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Uninett AS
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
A class that tries to retrieve all internal sensors from Geist-branded WeatherGoose
products.

Uses the vendor-specific GEIST-V4-MIB (derived from the IT-WATCHDOGS-V4-MIB)
to detect and collect sensor-information.

Please note:
This is NOT a full implementaion of the GEIST-V4-MIB. Only the internal
sensors of the box are implemented. The box can be extended with additional
external sensors, but these are not implemented because we did not have any
external sensors available at the time of this implementation.
"""

from nav.oids import OID
from nav.smidumps import get_mib
from .itw_mibv4 import ItWatchDogsMibV4


class GeistMibV4(ItWatchDogsMibV4):
    """
    A MibRetriever for retrieving information from Geist branded
    WeatherGoose products.

    Based on the GEIST-V4-MIB, which is more or less derived from the
    IT-WATCHDOGS-V4-MIB. Objects names in the derived MIB seems to be the
    same.

    """

    mib = get_mib('GEIST-V4-MIB')

    oid_name_map = {OID(attrs['oid']): name for name, attrs in mib['nodes'].items()}

    lowercase_nodes = {key.lower(): key for key in mib['nodes']}

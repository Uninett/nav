#
# Copyright (C) 2014 Uninett AS
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
"""Useful crap"""

from .statmodules import (StatCpuAverage, StatUptime, StatIfInOctets,
                          StatIfOutOctets, StatIfOutErrors, StatIfInErrors,
                          StatMinFreeAddresses)

CLASSMAP = {'cpu_routers_highestmax': StatCpuAverage,
            'uptime': StatUptime,
            'ifinoctets': StatIfInOctets,
            'ifoutoctets': StatIfOutOctets,
            'ifouterrors': StatIfOutErrors,
            'ifinerrors': StatIfInErrors,
            'leastfreeaddresses': StatMinFreeAddresses,
            }

TIMEFRAMES = (
    ('-1h', 'Last Hour'),
    ('-1d', 'Last Day'),
    ('-1w', 'Last Week'),
    ('-1month', 'Last Month'),
)

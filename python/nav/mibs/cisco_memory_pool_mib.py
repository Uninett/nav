#
# Copyright (C) 2013 Uninett AS
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
from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs import mibretriever

NAME = 'ciscoMemoryPoolName'
FREE = 'ciscoMemoryPoolFree'
USED = 'ciscoMemoryPoolUsed'
VALID = 'ciscoMemoryPoolValid'


class CiscoMemoryPoolMib(mibretriever.MibRetriever):
    mib = get_mib('CISCO-MEMORY-POOL-MIB')

    @defer.inlineCallbacks
    def get_memory_usage(self):
        """Retrieves memory usage stats from a Cisco device.

        :returns: A deferred whose result is a dict
                  {pool_name: (used_bytes, free_bytes)}

        """
        pools = yield self.retrieve_columns([NAME, VALID, USED, FREE])
        result = dict(
            (row[NAME], (row[USED], row[FREE])) for row in pools.values() if row[VALID]
        )
        return result

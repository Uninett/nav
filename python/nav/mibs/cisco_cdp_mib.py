#
# Copyright (C) 2012 Uninett AS
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
""" "CISCO-CDP-MIB handling"""

import socket
from collections import namedtuple

from twisted.internet import defer

from nav.ip import IP
from nav.mibs import reduce_index

from nav.smidumps import get_mib
from . import mibretriever

ADDRESS_TYPE_IP = 1


class CiscoCDPMib(mibretriever.MibRetriever):
    "A MibRetriever for handling CISCO-CDP-MIB"

    mib = get_mib('CISCO-CDP-MIB')

    def get_neighbors_last_change(self):
        """Retrieves the sysUpTime value of the last time the cdp neighbors
        table was changed.

        """
        return self.get_next('cdpGlobalLastChange')

    @defer.inlineCallbacks
    def get_cdp_neighbors(self):
        "Returns a list of CDPNeighbor objects from the device's cdpCacheTable"
        cache = yield self._get_cdp_cache_table()
        neighbors = []
        for index, row in cache.items():
            neighbor = self._make_cache_tuple(index, row)
            if neighbor:
                neighbors.append(neighbor)
        return neighbors

    @defer.inlineCallbacks
    def _get_cdp_cache_table(self):
        cache = yield self.retrieve_columns(
            [
                'cdpCacheAddressType',
                'cdpCacheAddress',
                'cdpCacheDeviceId',
                'cdpCacheDevicePort',
            ]
        )
        return reduce_index(cache)

    @staticmethod
    def _make_cache_tuple(index, row):
        if row['cdpCacheAddressType'] != ADDRESS_TYPE_IP:
            return
        ifindex, _deviceindex = index
        if row['cdpCacheAddress']:
            try:
                ipstring = socket.inet_ntoa(row['cdpCacheAddress'])
                ip = IP(ipstring)
            except (socket.error, ValueError):
                ip = None
        else:
            ip = None
        deviceid = row['cdpCacheDeviceId'] or None
        deviceport = row['cdpCacheDevicePort'] or None

        if not (ip or deviceid):
            # we have no idea how to identify this record, ignore it
            return
        return CDPNeighbor(ifindex, ip, deviceid, deviceport)


CDPNeighbor = namedtuple('CDPNeighbor', 'ifindex ip deviceid deviceport')

#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
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
"""HP STATISTICS-MIB"""

from collections import namedtuple
from IPy import IP
from twisted.internet import defer

from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index

MulticastStat = namedtuple("MulticastStat", "group ifindex vlan access")


class StatisticsMib(mibretriever.MibRetriever):
    """HP STATISTICS-MIB"""

    mib = get_mib('STATISTICS-MIB')

    @defer.inlineCallbacks
    def get_cpu_utilization(self):
        """Returns the current switch CPU utilization in percent"""
        util = yield self.get_next('hpSwitchCpuStat')
        if util is not None:
            return dict(cpu=util)

    def get_cpu_loadavg(self):
        return defer.succeed(None)

    @defer.inlineCallbacks
    def get_ipv4_multicast_groups_per_port(self):
        """
        Returns IGMP snooping information from ports.

        :returns: A Deferred whose result is a list of MulticastStat tuples
        """
        column = "hpIgmpStatsPortAccess2"
        ports = (
            yield self.retrieve_columns([column])
            .addCallback(self.translate_result)
            .addCallback(reduce_index)
        )

        def _split(item):
            index, columns = item
            vlan = index[0]
            group = index[1:5]
            ifindex = index[5]
            access = columns[column]
            return MulticastStat(
                IP('.'.join(str(i) for i in group)), ifindex, vlan, access
            )

        return [_split(i) for i in ports.items()]

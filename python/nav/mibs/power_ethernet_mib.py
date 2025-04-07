#
# Copyright (C) 2017 Uninett AS
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


class PowerEthernetMib(mibretriever.MibRetriever):
    mib = get_mib('POWER-ETHERNET-MIB')

    @defer.inlineCallbacks
    def get_groups_table(self):
        """Retrieves PoE group information"""
        cols = yield self.retrieve_columns(
            ["pethMainPsePower", "pethMainPseOperStatus", "pethMainPseConsumptionPower"]
        )
        return cols

    @defer.inlineCallbacks
    def get_ports_table(self):
        """Retrieves PoE port information"""
        cols = yield self.retrieve_table("pethPsePortTable")
        return cols

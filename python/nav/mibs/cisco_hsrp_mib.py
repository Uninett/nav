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
"""CISCO-HSRP-MIB handling"""

from IPy import IP
from twisted.internet import defer
from nav.smidumps import get_mib
from . import mibretriever


class CiscoHSRPMib(mibretriever.MibRetriever):
    """A MibRetriever for handling CISCO-HSRP-MIB"""

    mib = get_mib('CISCO-HSRP-MIB')

    @defer.inlineCallbacks
    def get_virtual_addresses(self):
        """Retrieves a map of virtual HSRP addresses->ifindex"""
        index_addrs = yield self.retrieve_column('cHsrpGrpVirtualIpAddr')
        addr_map = dict(
            (IP(ip), ifindex) for (ifindex, group), ip in index_addrs.items()
        )
        return addr_map

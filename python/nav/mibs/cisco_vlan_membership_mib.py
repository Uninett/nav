#
# Copyright (C) 2009 Uninett AS
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
"""MibRetriever for CISCO-VLAN-MEMBERSHIP-MIB"""
from __future__ import absolute_import
from twisted.internet import defer
from . import mibretriever


class CiscoVlanMembershipMib(mibretriever.MibRetriever):
    """MibRetriever for CISCO-VLAN-MEMBERSHIP-MIB"""
    from nav.smidumps.cisco_vlan_membership_mib import MIB as mib

    @defer.deferredGenerator
    def get_vlan_membership(self):
        """Get a mapping of access port ifindexes->VLAN"""
        dw = defer.waitForDeferred(self.retrieve_column('vmVlan'))
        yield dw
        vlans = dw.getResult()

        result = dict([(index[0], vlan)
                      for index, vlan in vlans.items()])
        yield result

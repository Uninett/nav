#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
""""handling of CISCO-VLAN-IFTABLE-RELATIONSHIP-MIB"""
from __future__ import absolute_import

from collections import namedtuple

from twisted.internet import defer

from . import mibretriever


class CiscoVlanIftableRelationshipMib(mibretriever.MibRetriever):
    """A CISCO-VLAN-IFTABLE-RELATIONSHIP-MIB MibRetriever"""
    from nav.smidumps.cisco_vlan_iftable_relationship_mib import MIB as mib

    @defer.inlineCallbacks
    def get_routed_vlan_ifindexes(self):
        """Retrieves a list of RoutedVlan named tuples.

        A physical_ifindex of 0, indicates that the vlan is not routed through
        a physical interface.

        """
        routed_vlans = yield self.retrieve_column('cviRoutedVlanIfIndex')
        result = [RoutedVlan(vlan, physical, virtual)
                  for (vlan, physical), virtual in routed_vlans.items()]
        defer.returnValue(result)

# pylint: disable=C0103
RoutedVlan = namedtuple('RoutedVlan', 'vlan physical virtual')

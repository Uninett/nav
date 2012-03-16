"handling of CISCO-VLAN-IFTABLE-RELATIONSHIP-MIB"

from twisted.internet import defer
from nav.namedtuple import namedtuple

import mibretriever

class CiscoVlanIftableRelationshipMib(mibretriever.MibRetriever):
    "A CISCO-VLAN-IFTABLE-RELATIONSHIP-MIB MibRetriever"
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

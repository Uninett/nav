from twisted.internet import defer
import mibretriever

class CiscoVlanMembershipMib(mibretriever.MibRetriever):
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

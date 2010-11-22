from nav.Snmp.pysnmp_se import Snmp
from nav.Snmp.errors import *

class SNMPHandler(object):
    netbox = ''
    ifAliasOid = '1.3.6.1.2.1.31.1.1.1.18' # From IF-MIB
    vlanOid = '1.3.6.1.2.1.17.7.1.4.5.1.1' # From Q-BRIDGE-MIB
    
    def __init__(self, netbox):
        self.netbox = netbox
    
    def __unicode__(self):
        return self.netbox.type.vendor.id

    def bulkwalk(self, oid):
        handle = Snmp(self.netbox.ip, self.netbox.read_only, self.netbox.snmp_version)
        result = []
        try:
            result = handle.bulkwalk(oid)
        except UnsupportedSnmpVersionError, e:
            result = handle.walk(oid)
            
        return result

    def getIfAlias(self, ifindex):
        pass
    
    def getAllIfAlias(self):
        return self.bulkwalk(self.ifAliasOid)
        
    def setIfAlias(self, ifindex, ifalias):
        pass
    
    def getVlan(self, ifindex):
        pass
    
    def getAllVlans(self):
        return self.bulkwalk(self.vlanOid)
    
    def setVlan(self, ifindex, vlan):
        pass
    

class Cisco(SNMPHandler):
    def __init__(self, netbox):
        super(Cisco, self).__init__(netbox)
        self.vlanOid = '1.3.6.1.4.1.9.9.68.1.2.2.1.2'


class HP(SNMPHandler):
    def __init__(self, netbox):
        super(HP, self).__init__(netbox)


class SNMPFactory(object):
     @classmethod
     def getInstance(self, netbox):
         if (netbox.type.vendor.id == 'cisco'):
             return Cisco(netbox)
         if(netbox.type.vendor.id == 'hp'):
             return HP(netbox)
         return SNMPHandler(netbox)
     
     def __init__(self):
         pass

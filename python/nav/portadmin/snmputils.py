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

    def _getLegalIfIndex(self, ifindex):
        if isinstance(ifindex, int):
            ifindex = str(ifindex)
        if not isinstance(ifindex, str):
            raise TypeError('Unlegal value for interface-index')
        if not ifindex.isdigit():
            raise TypeError('Unlegal value for interface-index')
        return ifindex

    def _getQuery(self, oid, ifindex):
        return oid + "." + self._getLegalIfIndex(ifindex)

    def _getReadOnlyHandle(self):
        return Snmp(self.netbox.ip, self.netbox.read_only)

    def _queryNetbox(self, oid, ifindex):
        handle = self._getReadOnlyHandle()
        result = None
        try:
            result = handle.get(self._getQuery(oid, ifindex))
        except NoSuchObjectError, e:
            pass
        return result

    def _getReadWriteHandle(self):
        return Snmp(self.netbox.ip, self.netbox.read_write,
                        self.netbox.snmp_version)

    def _setNetboxValue(self, oid, ifindex, valueType, value):
        handle = self._getReadWriteHandle()
        return handle.set(self._getQuery(oid, ifindex), valueType, value)

    def getIfAlias(self, ifindex):
        return self._queryNetbox(self.ifAliasOid, ifindex)

    def getAllIfAlias(self):
        return self.bulkwalk(self.ifAliasOid)
        
    def setIfAlias(self, ifindex, ifalias):
        if not isinstance(ifalias, str):
            raise TypeError('Unlegal value for interface-alias')
        return self._setNetboxValue(self.ifAliasOid, ifindex, "s", ifalias)

    def getVlan(self, ifindex):
        return self._queryNetbox(self.vlanOid, ifindex)

    def getAllVlans(self):
        return self.bulkwalk(self.vlanOid)
    
    def setVlan(self, ifindex, vlan):
        if isinstance(vlan, str):
            if vlan.isdigit():
                vlan = int(vlan)
        if not isinstance(vlan, int):
            raise  TypeError('Unlegal value for vlan')
        return self._setNetboxValue(self.vlanOid, ifindex, "i", vlan)

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

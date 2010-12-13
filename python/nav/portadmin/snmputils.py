import time
from nav.Snmp.pysnmp_se import Snmp
from nav.Snmp.errors import *
from nav.bitvector import BitVector
from nav.models.manage import SwPortAllowedVlan

class SNMPHandler(object):
    netbox = ''
    ifAliasOid = '1.3.6.1.2.1.31.1.1.1.18' # From IF-MIB
    vlanOid = '1.3.6.1.2.1.17.7.1.4.5.1.1' # From Q-BRIDGE-MIB
    # oid for reading vlans om a stndard netbox (not cisco)
    dot1qVlanStaticRowStatus = '1.3.6.1.2.1.17.7.1.4.3.1.5'
    # List of all ports on a vlan as a hexstring
    dot1qVlanStaticEgressPorts = '1.3.6.1.2.1.17.7.1.4.3.1.2'
    ifAdminStatus = '1.3.6.1.2.1.2.2.1.7'
    ifOperStatus  = '1.3.6.1.2.1.2.2.1.8'

    def __init__(self, netbox):
        self.netbox = netbox
        self.readOnlyHandle = None
        self.readWriteHandle = None
    
    def __unicode__(self):
        return self.netbox.type.vendor.id

    def _bulkwalk(self, oid):
       handle = self._getReadOnlyHandle()
       result = []
       try:
           result = handle.bulkwalk(oid)
       except UnsupportedSnmpVersionError, e:
           result = handle.walk(oid)
       return result

    def _getLegalIfIndex(self, ifindex):
        if isinstance(ifindex, int):
            ifindex = str(ifindex)
        if not (isinstance(ifindex, str) or isinstance(ifindex, unicode)):
            raise TypeError('Illegal value for interface-index')
        if not ifindex.isdigit():
            raise TypeError('Illegal value for interface-index')
        return ifindex

    def _getQuery(self, oid, ifindex):
        return oid + "." + self._getLegalIfIndex(ifindex)

    def _getReadOnlyHandle(self):
        if self.readOnlyHandle is None:
            self.readOnlyHandle = Snmp(self.netbox.ip, self.netbox.read_only)
        return self.readOnlyHandle

    def _queryNetbox(self, oid, ifindex):
        handle = self._getReadOnlyHandle()
        result = None
        try:
            result = handle.get(self._getQuery(oid, ifindex))
        except NoSuchObjectError, e:
            pass
        return result

    def _getReadWriteHandle(self):
        if self.readWriteHandle is None:
            self.readWriteHandle = Snmp(self.netbox.ip,
                                        self.netbox.read_write,
                                        self.netbox.snmp_version)
        return self.readWriteHandle

    def _setNetboxValue(self, oid, ifindex, valueType, value):
        handle = self._getReadWriteHandle()
        return handle.set(self._getQuery(oid, ifindex), valueType, value)

    def getIfAlias(self, ifindex):
        """ Get alias on a specific interface """
        return self._queryNetbox(self.ifAliasOid, ifindex)

    def getAllIfAlias(self):
        return self._bulkwalk(self.ifAliasOid)
        
    def setIfAlias(self, ifindex, ifalias):
        """ Set alias on a specific interface."""
        if not (isinstance(ifalias, str) or isinstance(ifalias, unicode)):
            raise TypeError('Illegal value for interface-alias: %s' %ifalias)
        return self._setNetboxValue(self.ifAliasOid, ifindex, "s", ifalias)

    def getVlan(self, ifindex):
        """ Get vlan on a specific interface."""
        return self._queryNetbox(self.vlanOid, ifindex)

    def getAllVlans(self):
        return self._bulkwalk(self.vlanOid)
    
    def _computeOctetString(self, hexstring, port, action='enable'):
        """
        hexstring: the returnvalue of the snmpquery
        port: the number of the port to add
        """
        bit = BitVector(hexstring)
        # Add port to string
        port = port - 1
        if action == 'enable':
            bit[port] = 1
        else:
            bit[port] = 0
        return str(bit)

    def setVlan(self, ifindex, vlan):
        if isinstance(vlan, str) or isinstance(vlan, unicode):
            if vlan.isdigit():
                vlan = int(vlan)
        if not isinstance(vlan, int):
            raise TypeError('Illegal value for vlan: %s' %vlan)
        # Fetch current vlan
        fromvlan = self.getVlan(ifindex)
        # fromvlan and vlan is the same, there's nothing to do
        if fromvlan == vlan:
            return None
        # Add port to vlan. This makes the port active on both old and new vlan
        status = self._setNetboxValue(self.vlanOid, ifindex, "u", vlan)
        # Remove port from list of ports on old vlan
        hexstring = self._queryNetbox(self.dot1qVlanStaticEgressPorts, fromvlan)
        modified_hexport = self._computeOctetString(hexstring, ifindex, 'disable')
        return self._setNetboxValue(self.dot1qVlanStaticEgressPorts, fromvlan, 's', modified_hexport)


    def setIfUp(self, ifindex):
        """Set interface.to up"""
        return self._setNetboxValue(self.ifAdminStatus, ifindex, "i", 1)

    def setIfDown(self, ifindex):
        """Set interface.to down"""
        return self._setNetboxValue(self.ifAdminStatus, ifindex, "i", 2)

    def restartIf(self, ifindex, wait=5):
        """ Take interface down and up.
            wait = number of seconds to wait between down and up."""
        if isinstance(wait, str) or isinstance(wait, unicode):
            if wait.isdigit():
                wait = int(wait)
        if not isinstance(wait, int):
            raise TypeError('Illegal value for wait: %s' %wait)
        self.setIfDown(ifindex)
        time.sleep(wait)
        self.setIfUp(ifindex)

    def getIfAdminStatus(self, ifindex):
        return self._queryNetbox(self.ifAdminStatus, ifindex)

    def getIfOperStatus(self, ifindex):
        return self._queryNetbox(self.ifOperStatus, ifindex)

    def _getLastNumber(self, oid):
        if not (isinstance(oid, str) or isinstance(oid, unicode)):
            raise TypeError('Illegal value for oid')
        splits = oid.split('.')
        last = splits[-1]
        if isinstance(last, str):
            if last.isdigit():
                last = int(last)
        return last

    def _getIfStats(self, stats):
        available_stats = []
        for (ifIndex, stat) in stats:
            ifIndex = self._getLastNumber(ifIndex)
            if isinstance(ifIndex, int):
                available_stats.append((ifIndex, stat))
        return available_stats
            
    def getNetboxAdminStatus(self):
        ifAdminStats = self._bulkwalk(self.ifAdminStatus)
        return self._getIfStats(ifAdminStats)

    def getNetboxOperStatus(self):
        ifOperStats = self._bulkwalk(self.ifOperStatus)
        return self._getIfStats(ifOperStats)

    def _filter_vlans(self, vlans):
        vlans = filter(None, list(set(vlans)))
        vlans.sort()
        return vlans

    def getNetboxVlans(self):
        boxVlans = self._bulkwalk(self.dot1qVlanStaticRowStatus)
        available_vlans = []
        for (vlan, valueType) in boxVlans:
            currVlan = self._getLastNumber(vlan)
            if isinstance(currVlan, int):
                available_vlans.append(currVlan)
        # remove duplicates and none values
        available_vlans = self._filter_vlans(available_vlans)
        return available_vlans

class Cisco(SNMPHandler):
    def __init__(self, netbox):
        super(Cisco, self).__init__(netbox)
        self.vlanOid = '1.3.6.1.4.1.9.9.68.1.2.2.1.2'

    def getNetboxVlans(self):
        """ Find all available vlans on this netbox"""
        available_vlans = []
        for swport in self.netbox.get_swports():
            if swport.trunk:
                available_vlans.extend(self._find_vlans_on_trunk(swport))
            else:
                available_vlans.append(swport.vlan)
        # remove duplicates and none values
        available_vlans = self._filter_vlans(available_vlans)
        return available_vlans

    def _find_vlans_on_trunk(self, swport):
        """Find all vlans on trunk-ports"""
        port = SwPortAllowedVlan.objects.get(interface=swport.id)
        vector = BitVector.from_hex(port.hex_string)
        vlans = vector.get_set_bits()
        return vlans
        
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

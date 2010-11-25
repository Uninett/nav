import re

from nav.models.manage import SwPortAllowedVlan
from nav.models.manage import Vlan
from nav.models.profiles import AccountGroup
from operator import attrgetter
from nav.bitvector import BitVector
from nav.portadmin.snmputils import *

def get_and_populate_livedata(netbox, swports):
    # Fetch live data from netbox
    handler = SNMPFactory.getInstance(netbox)
    live_ifaliases = create_dict_from_tuplelist(handler.getAllIfAlias())
    live_vlans = create_dict_from_tuplelist(handler.getAllVlans())
    update_swports_with_snmpdata(swports, live_ifaliases, live_vlans)

def create_dict_from_tuplelist(tuplelist):
    """
    The input is a list from a snmp bulkwalk or walk.
    Extract ifindex from oid and use that as key in the dict.
    """
    pattern = re.compile("(\d+)$")
    result = []
    # Extract ifindex from oid
    for key, value in tuplelist:
        m = pattern.search(key)
        if m:
            ifindex = int(m.groups()[0])
            result.append((ifindex, value))

    # Create dict from modified list            
    return dict(result)

def update_swports_with_snmpdata(swports, ifalias, vlans):
    """
    Update the swports with data gathered via snmp.
    """
    for swport in swports:
        if ifalias.has_key(swport.ifindex):
            swport.ifalias = ifalias[swport.ifindex]
        if vlans.has_key(swport.ifindex):
            swport.vlan = vlans[swport.ifindex]

def find_and_populate_allowed_vlans(account, netbox, swports):
    allowed_vlans = find_allowed_vlans_for_user_on_netbox(account, netbox)
    set_editable_on_swports(swports, allowed_vlans)
    return allowed_vlans    

def find_allowed_vlans_for_user_on_netbox(account, netbox):
    allowed_vlans = []
    netbox_vlans = find_vlans_on_netbox(netbox)
    if is_administrator(account):
        allowed_vlans = netbox_vlans
    else:
        all_allowed_vlans = find_allowed_vlans_for_user(account)
        allowed_vlans = intersect(all_allowed_vlans, netbox_vlans)
    
    return sorted(allowed_vlans)

def find_vlans_on_netbox(netbox):
    fac = SNMPFactory.getInstance(netbox) 
    return fac.getNetboxVlans()
    
def find_allowed_vlans_for_user(account):
    allowed_vlans = []
    for org in account.organizations.all():
        allowed_vlans.extend([vlan.vlan for vlan in find_vlans_in_org(org)])
    allowed_vlans.sort()
    return allowed_vlans

def set_editable_on_swports(swports, vlans):
    """
    Set a flag on the swport to indicate if user is allowed to edit it.
    """
    for swport in swports:
        if swport.vlan in vlans and not swport.trunk :
            swport.iseditable = True
        else:
            swport.iseditable = False

def intersect(a, b):
    return list(set(a) & set(b))
        
def find_vlans_in_org(org):
    return org.vlan_set.all()

def is_administrator(account):
    groups = account.get_groups()
    if AccountGroup.ADMIN_GROUP in groups:
        return True
    return False

def get_netident_for_vlans(inputlist):
    """
    Fetch net_ident for the vlans in the input
    If it does not exist, fill in blanks
    """
    result = []
    for vlan in inputlist:
        vlanlist = Vlan.objects.filter(vlan=vlan)
        if vlanlist:
            for element in vlanlist:
                result.append((element.vlan, element.net_ident))
        else:
            result.append((vlan, ''))
        
    return result
import re

from nav.models.manage import SwPortAllowedVlan
from operator import attrgetter
from nav.bitvector import BitVector

def find_vlans_on_netbox(netbox):
    """
    Fetch all vlans from all interfaces and trunks on the netbox
    """
    available_vlans = []
    for swport in netbox.get_swports():
        if swport.trunk:
            available_vlans.extend(find_vlans_on_trunk(swport))
        else:
            available_vlans.append(swport.vlan)
    available_vlans = list(set(available_vlans)) # remove duplicates
    return available_vlans
    
def find_vlans_on_trunk(swport):
    port = SwPortAllowedVlan.objects.get(interface=swport.id)
    vector = BitVector.from_hex(port.hex_string)
    vlans = vector.get_set_bits()
    return vlans
    
def find_allowed_vlans_for_user(account):
    allowed_vlans = []
    for org in account.organizations.all():
        allowed_vlans.extend([vlan.vlan for vlan in find_vlans_in_org(org)])
    allowed_vlans.sort()
    return allowed_vlans

def find_allowed_vlans_for_user_on_netbox(account, netbox):
    all_allowed_vlans = find_allowed_vlans_for_user(account)
    netbox_vlans = find_vlans_on_netbox(netbox)
    allowed_vlans = intersect(all_allowed_vlans, netbox_vlans)
    return allowed_vlans

def intersect(a, b):
    return list(set(a) & set(b))
        
def find_vlans_in_org(org):
    return org.vlan_set.all()

def create_dict_from_tuplelist(tuplelist):
    pattern = re.compile("(\d+)$")
    result = []
    for key, value in tuplelist:
        m = pattern.search(key)
        if m:
            ifindex = int(m.groups()[0])
            result.append((ifindex, value))
            
    return dict(result)

def update_swports_with_snmpdata(swports, ifalias, vlans):
    for swport in swports:
        live_ifalias = ifalias[swport.ifindex]
        live_vlan = vlans[swport.ifindex] 
        if live_ifalias:
            swport.ifalias = live_ifalias
        if live_vlan:
            swport.vlan = live_vlan
            

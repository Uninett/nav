# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Kristian Klette <kristian.klette@uninett.no>
#

__copyright__ = "Copyright 2007-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Kristian Klette (kristian.klette@uninett.no)"
__id__ = "$Id$"

import datetime
import socket
import sys

from django.db.models import Q

from nav.django.shortcuts import render_to_response, object_list
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, Module, SwPort, GwPort, Cam, Arp, GwPortPrefix, SwPortVlan, Vlan
from nav.models.service import Service


def search_expand_swport(swportid=None, swport=None, scanned = []):
    """
    Expands all paths to a switch port
    """
    if not scanned:
        scanned = []

    if not swport:
        try:
            swport = SwPort.objects.get(id=swportid)
        except SwPort.DoesNotExist:
            return ([],[])

    found_swports = []
    found_gwports = []

    # Find gwport that has the same vlan
    for swportvlan in swport.swportvlan_set.exclude(vlan__net_type='static').select_related(depth=5):
        for prefix in swportvlan.vlan.prefix_set.all():
            for gwportprefix in prefix.gwportprefix_set.all():
                found_gwports.append(gwportprefix.gwport)

    for port in SwPort.objects.filter(to_swport=swport).exclude(to_swport__in=scanned).select_related(depth=5):
        scanned.append(port)

        found_swports.append(port)

        recurs_found = search_expand_swport(swport=port, scanned=scanned)
        found_gwports.extend(recurs_found[0])
        found_swports.extend(recurs_found[1])
    
    for port in GwPort.objects.filter(to_swport__in=found_swports):
        found_gwports.append(port)
    
    for port in GwPort.objects.filter(to_netbox=swport.module.netbox):
        found_gwports.append(port)
    
    for port in GwPort.objects.filter(to_swport=swport):
        found_gwports.append(port)

    return (found_gwports, found_swports)

def search_expand_netbox(netboxid=None, netbox=None):
    """
    Expands all paths to a router from a netboxid
    """
    
    found_gwports = []
    found_swports = []
    
    if not netbox:
        try:
            netbox = Netbox.objects.get(id=netboxid)
        except Netbox.DoesNotExist:
            return ([],[])

    for result in netbox.get_uplinks():
        if result['other'].__class__ == GwPort:
            found_gwports.append(result['other'])
        else:
            found_swports.append(result['other'])

    gwports = GwPort.objects.filter(to_netbox=netbox)
    swports = SwPort.objects.filter(to_netbox=netbox)

    found_gwports.extend(gwports)

    for swport in swports:
        found_swports.append(swport)
        ses = search_expand_swport(swport=swport)
        found_gwports.extend(ses[0])
        found_swports.extend(ses[1])
    

    return (found_gwports, found_swports)



def search_expand_sysname(sysname=None):
    """
    """

    if not sysname:
        return ([],[])

    try:
        netbox = Netbox.objects.get(sysname=sysname)
    except Netbox.DoesNotExist:
        return ([],[])

    return search_expand_netbox(netbox=netbox)


def search_expand_mac(mac=None):
    """
    """

    if not mac:
        return ([],[])

    import re
    if not re.match('^([a-fA-F0-9]{2}[:|\-]?){6}$', mac):
        return ([],[])

    found_swports = []
    found_gwports = []
    
    cam_entries = Cam.objects.filter(mac=mac, end_time__gte=datetime.datetime.max).select_related(depth=5)

    for cam_entry in cam_entries:
        for swport in SwPort.objects.filter(module__netbox=cam_entry.netbox, module__module_number=cam_entry.module, interface=cam_entry.port).select_related(depth=5):
            found_swports.append(swport)
            swport_search = search_expand_swport(swport=swport)
            found_gwports.extend(swport_search[0])
            found_swports.extend(swport_search[1])

    return (found_gwports, found_swports)


# Search functions

def sysname_search(sysname, exact=False):
    """
    Searches the database for any connections to the sysname
    """
    router_matches = []
    gwport_matches = []
    swport_matches = []
    
    if exact:
        routers = Netbox.objects.filter(sysname=sysname, category__in=['GW','GSW'])
        netboxes = Netbox.objects.filter(sysname=sysname)
    else:
        routers = Netbox.objects.filter(sysname__icontains=sysname, category__in=['GW','GSW'])
        netboxes = Netbox.objects.filter(sysname__icontains=sysname)


    for router in routers:
        router_matches.append(router)

    for netbox in netboxes:
        netbox_search = search_expand_netbox(netbox=netbox)
        gwport_matches.extend(netbox_search[0])
        swport_matches.extend(netbox_search[1])

    for gwport in GwPort.objects.all().filter(module__netbox__in=netboxes):
        gwport_matches.append(gwport)
    
    
    for swport in SwPort.objects.filter(module__netbox__in=netboxes):
        swport_matches.append(swport)

        swport_search = search_expand_swport(swport=swport)
        gwport_matches.extend(swport_search[0])
        swport_matches.extend(swport_search[1])
    
    router_matches.extend([gwport.module.netbox for gwport in gwport_matches])

    router_matches = list(set(router_matches))
    swport_matches = list(set(swport_matches))
    gwport_matches = list(set(gwport_matches))

    return (router_matches, gwport_matches, swport_matches)

def ip_search(ip, exact=False):
    """
    Searches the database for anything related to the ip

    Returns a list of (routers, gwports, swports)
    """

    router_matches = []
    gwport_matches = []
    swport_matches = []

    if exact:
        netboxes = Netbox.objects.filter(ip=ip)
        gwportprefixes = GwPortPrefix.objects.filter(gw_ip=ip)
        arp_entries = Arp.objects.filter(ip=ip, end_time__gte=datetime.datetime.max)
    else:
        netboxes = Netbox.objects.filter(ip__contains=ip)
        gwportprefixes = GwPortPrefix.objects.filter(gw_ip__contains=ip)
        arp_entries = Arp.objects.filter(ip__contains=ip, end_time__gte=datetime.datetime.max)

    # Add matching routers
    router_matches.extend([netbox for netbox in netboxes.filter(category__in=['GW','GSW'])])
    
    for netbox in netboxes:
        netbox_search = search_expand_netbox(netbox=netbox)
        gwport_matches.extend(netbox_search[0])
        swport_matches.extend(netbox_search[1])

    for prefix in gwportprefixes:
        gwport_matches.append(prefix.gwport)

    for arp_entry in arp_entries:
        mac_search = search_expand_mac(mac=arp_entry.mac)
        gwport_matches.extend(mac_search[0])
        swport_matches.extend(mac_search[1])
    
    router_matches.extend([gwport.module.netbox for gwport in gwport_matches])
    
    router_matches = list(set(router_matches))
    swport_matches = list(set(swport_matches))
    gwport_matches = list(set(gwport_matches))

    return (router_matches, gwport_matches, swport_matches)

def portname_search(portname, exact=False):
    """
    """

    router_matches = []
    gwport_matches = []
    swport_matches = []

    if exact:
        swport_matches.extend(SwPort.objects.filter(port_name=portname))
    else:
        swport_matches.extend(SwPort.objects.filter(port_name__icontains=portname))

    for swport in [swport for swport in swport_matches if swport]:
        swport_search = search_expand_swport(swport=swport)
        gwport_matches.extend(swport_search[0])
        swport_matches.extend(swport_search[1])

    router_matches.extend([gwport.module.netbox for gwport in gwport_matches])
    
    router_matches = list(set(router_matches))
    swport_matches = list(set(swport_matches))
    gwport_matches = list(set(gwport_matches))

    return (router_matches, gwport_matches, swport_matches)

def room_search(room, exact=False):
    """
    """

    router_matches = []
    gwport_matches = []
    swport_matches = []

    if exact:
        swport_matches.extend(SwPort.objects.filter(module__netbox__room__id=room))
    else:
        swport_matches.extend(SwPort.objects.filter(module__netbox__room__id__icontains=room))
    
    for swport in [swport for swport in swport_matches if swport]:
        swport_search = search_expand_swport(swport=swport)
        gwport_matches.extend(swport_search[0])
        swport_matches.extend(swport_search[1])

    router_matches.extend([gwport.module.netbox for gwport in gwport_matches])
    
    router_matches = list(set(router_matches))
    swport_matches = list(set(swport_matches))
    gwport_matches = list(set(gwport_matches))

    return (router_matches, gwport_matches, swport_matches)


def mac_search(mac):
    """
    """

    router_matches = []
    gwport_matches = []
    swport_matches = []

    search  = search_expand_mac(mac)
    gwport_matches = search[0]
    swport_matches = search[1]
    router_matches = [gwport.module.netbox for gwport in gwport_matches]
    
    router_matches = list(set(router_matches))
    swport_matches = list(set(swport_matches))
    gwport_matches = list(set(gwport_matches))

    return (router_matches, gwport_matches, swport_matches)

def vlan_search(vlan, exact=False):
    """
    """

    router_matches = []
    gwport_matches = []
    swport_matches = []

    if exact:
        for swportvlan in SwPortVlan.objects.filter(vlan__vlan=vlan):
            swport_search = search_expand_swport(swport=swportvlan.swport)
            gwport_matches.extend(swport_search[0])
            swport_matches.extend(swport_search[1])

        for gwportprefix in GwPortPrefix.objects.filter(prefix__vlan__vlan=vlan).exclude(prefix__vlan__net_type='static'):
            gwport_matches.append(gwportprefix.gwport)

        for netbox in Netbox.objects.filter(prefix__vlan__vlan=vlan).exclude(prefix__vlan__net_type='static'):
            netbox_search = search_expand_netbox(netbox=netbox)
            gwport_matches.extend(netbox_search[0])
            swport_matches.extend(netbox_search[1])
    else:
        for swportvlan in SwPortVlan.objects.filter(vlan__vlan__icontains=vlan):
            swport_search = search_expand_swport(swport=swportvlan.swport)
            gwport_matches.extend(swport_search[0])
            swport_matches.extend(swport_search[1])

        for gwportprefix in GwPortPrefix.objects.filter(prefix__vlan__vlan__icontains=vlan).exclude(prefix__vlan__net_type='static'):
            gwport_matches.append(gwportprefix.gwport)

        for netbox in Netbox.objects.filter(prefix__vlan__vlan__iconatains=vlan).exclude(prefix__vlan__net_type='static'):
            netbox_search = search_expand_netbox(netbox=netbox)
            gwport_matches.extend(netbox_search[0])
            swport_matches.extend(netbox_search[1])


    router_matches = [gwport.module.netbox for gwport in gwport_matches]
    
    router_matches = list(set(router_matches))
    swport_matches = list(set(swport_matches))
    gwport_matches = list(set(gwport_matches))

    return (router_matches, gwport_matches, swport_matches)

        
   
    

#
# Copyright (C) 2007-2008 UNINETT AS
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
"""Network Explorer view functions"""

import datetime
import socket
import sys
from urllib import unquote

from django.http import HttpResponse, Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

import nav.models.cabling
from nav.models.manage import Netbox, Cam, Arp, GwPortPrefix, SwPortVlan
from nav.models.manage import Interface
import nav.models.service

import nav.natsort

from search import sysname_search, ip_search, mac_search, room_search
from search import vlan_search, portname_search

PATH = [("Home", "/"), ("Network Explorer", "/networkexplorer/")]

def index(request):
    """Basic view of the network"""

    routers = Netbox.objects.all().filter(category__in=['GW', 'GSW'])
    for router in routers:
        if len(router.get_gwports()) > 0:
            router.has_children = True
    return render_to_response(
        'networkexplorer/base.html',
        {
            'routers': routers,
            'navpath': PATH,
        },
        context_instance=RequestContext(request))

def expand_router(request):
    """
    Returns children of an router according to spec
    """
    router = get_object_or_404(Netbox, id=request.GET['netboxid'])
    gwports = router.get_gwports()
    interface_names = [p.ifname for p in gwports]
    unsorted = dict(zip(interface_names, gwports))
    interface_names.sort(key=nav.natsort.split)
    sorted_ports = [unsorted[i] for i in interface_names]

    for gwport in sorted_ports:
        gwport.prefixes = []
        # Check if the port is expandable
        gpp = GwPortPrefix.objects.filter(interface__id=gwport.id).exclude(prefix__vlan__net_type='static')
        for prefix in gpp:
            netmask_pos = prefix.prefix.net_address.find('/')
            netmask = prefix.prefix.net_address[netmask_pos:]
            prefix.display_addr = prefix.gw_ip + netmask
            gwport.prefixes.append(prefix)

            vlans = prefix.prefix.vlan.swportvlan_set.exclude(vlan__net_type='static').filter(interface__netbox=gwport.netbox)
            for vlan in vlans:
                if not vlan.interface.swportblocked_set.filter(vlan=vlan.vlan.vlan).count():
                    gwport.has_children = True

        gwport.prefixes.sort()
        if gwport.to_netbox:
            continue
        if gwport.to_interface:
            gwport.to_netbox = gwport.to_interface.netbox
            continue
        # Find connection trough prefixes
        try:
            for gwprefix in gwport.gwportprefix_set.exclude(prefix__vlan__net_type='static'):
                for prefix in prefix.gwportprefix_set.all().exclude(
                        interface=gwport, prefix__vlan_net_type='static'):
                    gwport.to_netbox = prefix.interface.netbox
                    raise StopIteration # Ugly hack since python doesnt support labeled breaks
        except:
            continue

    return render_to_response('networkexplorer/expand_router.html',
        {
            'sysname': router.sysname,
            'ports': sorted_ports,
        })

def expand_gwport(request):
    """
    """
    gwport = get_object_or_404(Interface, id=request.GET['gwportid'])
    sys.stderr.write("Expanding gwport %s\n" % gwport)
    sys.stderr.flush()
    vlans = []
    foreign_netboxes = []
    prefixes = gwport.gwportprefix_set.all().exclude(prefix__vlan__net_type='static')
    sys.stderr.write("- Found %s gwportprefixes\n" % len(prefixes))
    sys.stderr.flush()
    for prefix in prefixes:
        sys.stderr.write("-- Scanning prefix %s\n" % prefix)
        sys.stderr.flush()
        for vlan in prefix.prefix.vlan.swportvlan_set.all().filter(
                        interface__netbox=gwport.netbox
                        ).order_by('interface__ifname'):

            sys.stderr.write("--- Checking vlan %s\n" % vlan)
            sys.stderr.flush()
            # Check if port is spanningtreeblocked
            sys.stderr.write("---- Blocked: ")
            if vlan.interface.swportblocked_set.filter(vlan=vlan.vlan.vlan).count():
                sys.stderr.write(" yes. skipping this vlan\n")
                sys.stderr.flush()
                continue
            sys.stderr.write(" no.\n")
            sys.stderr.flush()
            if vlan and not vlan in vlans:
                vlan.interface.has_children = False
                sys.stderr.write("---- Checking for services\n")
                sys.stderr.flush()
                if vlan.interface.to_netbox and vlan.interface.to_netbox.service_set.all().count() > 0:
                    sys.stderr.write("----- Netbox %s has services\n" % vlan.interface.to_netbox)
                    sys.stderr.flush()
                    vlan.interface.has_children = True
                    vlan.interface.has_services = True
                sys.stderr.write("---- Checking for cam-entries\n")
                sys.stderr.flush()
                a= Cam.objects.filter(\
                        netbox=vlan.interface.netbox,\
                        ifindex=vlan.interface.ifindex,\
                        end_time__gt=datetime.datetime.max)
                if a.count() > 0:

                    sys.stderr.write("----- Found cam-entry\n\n %s \n\n" % a.query)
                    sys.stderr.flush()
                    vlan.interface.has_children = True
                sys.stderr.write("---- Checking for connected swport\n")
                sys.stderr.flush()
                if vlan.interface.to_interface:
                    sys.stderr.write("----- Found swport %s\n" % vlan.interface.to_interface)
                    sys.stderr.flush()
                    if vlan.interface.to_interface.netbox.category.id in ('SW','GSW','EDGE'):
                        vlan.interface.has_children = True
                        vlan.interface.connected_to_switch = True
                    if vlan.interface.to_interface.netbox.service_set.all().count():
                        vlan.interface.has_children = True
                    if Cam.objects.filter( \
                                                netbox=vlan.interface.to_interface.netbox, \
                                                ifindex=vlan.interface.to_interface.ifindex,\
                                                end_time__gt=datetime.datetime.max \
                                                ).count() > 0:
                        vlan.interface.has_children = True
                sys.stderr.write("vlan %s has_children = %s\n" % (vlan, vlan.interface.has_children))
                sys.stderr.flush()
                vlans.append(vlan)
                sys.stderr.write("Appended vlan %s to vlans - current len: %s\n" %(vlan, len(vlans)))
                sys.stderr.flush()
                foreign_netboxes.append(vlan.interface.netbox)
                sys.stderr.write("Appended netbox %s to f.netboxes - current len: %s\n" %(vlan.interface.netbox, len(foreign_netboxes)))
                sys.stderr.flush()
    sys.stderr.write("Sorting swports by interface\n")
    sys.stderr.flush()
    interface_names = [p.interface.ifname for p in vlans]
    unsorted = dict(zip(interface_names, vlans))
    interface_names.sort(key=nav.natsort.split)
    vlans = [unsorted[i] for i in interface_names]

    return render_to_response('networkexplorer/expand_gwport.html',
        {
            'gwport': gwport,
            'vlans': vlans,
        })

def expand_switch(request):
    """
    """
    switch = get_object_or_404(Netbox, id=request.GET['netboxid'])
    vlan = request.GET['vlanid'] or None
    swports = switch.get_swports()
    swportvlans = SwPortVlan.objects.filter(interface__in=swports,vlan__id=vlan)

    for swportvlan in swportvlans:
        if swportvlan.interface.to_interface:
            if swportvlan.interface.netbox.service_set.all().count() > 0:
                swportvlan.interface.has_children = True
                continue
        if Cam.objects.filter(
            netbox=swportvlan.interface.netbox,
            ifindex=swportvlan.interface.ifindex,
            end_time__gt=datetime.datetime.max).count() > 0:
            swportvlan.interface.has_children = True

    interface_names = [p.interface.ifname for p in swportvlans]
    unsorted = dict(zip(interface_names, swportvlans))
    interface_names.sort(key=nav.natsort.split)
    vlans = [unsorted[i] for i in interface_names]

    return render_to_response('networkexplorer/expand_switch.html',
        {
            'swportvlans': vlans,
        })


def expand_swport(request):
    """
    """
    swport = get_object_or_404(Interface, id=request.GET['swportid'])
    if swport.to_netbox:
        to_netbox = swport.to_netbox
    elif swport.to_interface:
        to_netbox = swport.to_interface.netbox
    else:
        to_netbox = None

    if to_netbox:
        services = to_netbox.service_set.all()
    else:
        services = []

    active_macs = Cam.objects.filter(netbox=swport.netbox, ifindex=swport.ifindex, end_time__gt=datetime.datetime.max)
    hosts_behind_port = []
    for mac in active_macs:
        arp_entries = Arp.objects.filter(mac=mac.mac, end_time__gt=datetime.datetime.max)
        for arp_entry in arp_entries:
            try:
                hostname = socket.gethostbyaddr(arp_entry.ip)[0]
            except:
                hostname = None
            if hostname:
                host_string = "%s (%s) [<a href=\"/machinetracker/mac?mac=%s&days=7\" target=\"_blank\">%s</a>]" % (hostname, arp_entry.ip, mac.mac, mac.mac)
            else:
                host_string = " %s [<a href=\"/machinetracker/mac?mac=%s&days=7\" target=\"_blank\">%s</a>]" % (arp_entry.ip, mac.mac, mac.mac)
            if host_string not in hosts_behind_port:
                hosts_behind_port.append(host_string)
        if len(arp_entries) < 1 and mac.mac not in hosts_behind_port:
            hosts_behind_port.append(mac.mac)
    hosts_behind_port.sort()


    return render_to_response('networkexplorer/expand_swport.html',
        {
            'netbox': to_netbox,
            'services': services,
            'active_hosts': hosts_behind_port,
        })


def search(request):
    """
    """
    # Raise 404 if no parameters are given
    if 'lookup_field' not in request.GET:
        raise Http404

    router_matches = []
    gwport_matches = []
    swport_matches = []
        
    if request.REQUEST.get('exact', None) == 'on':
        exact = True
    else:
        exact = False

    if request.GET['lookup_field'] == 'sysname':
        result = sysname_search(request.GET['query'], exact)
        router_matches = result[0]
        gwport_matches = result[1]
        swport_matches = result[2]

    if request.GET['lookup_field'] == 'ip':
        result = ip_search(request.GET['query'], exact)
        router_matches = result[0]
        gwport_matches = result[1]
        swport_matches = result[2]

    if request.GET['lookup_field'] == 'mac':
        result = mac_search(unquote(request.GET['query']))
        router_matches = result[0]
        gwport_matches = result[1]
        swport_matches = result[2]
    
    if request.GET['lookup_field'] == 'room':
        result = room_search(request.GET['query'], exact)
        router_matches = result[0]
        gwport_matches = result[1]
        swport_matches = result[2]
    
    if request.GET['lookup_field'] == 'vlan':
        result = vlan_search(request.GET['query'], exact)
        router_matches = result[0]
        gwport_matches = result[1]
        swport_matches = result[2]
    
    if request.GET['lookup_field'] == 'port':
        result = portname_search(request.GET['query'], exact)
        router_matches = result[0]
        gwport_matches = result[1]
        swport_matches = result[2]


    # A bit ugly hack to remove duplicates, but simplejson doesnt seem to support sets
    router_matches = list(set(router_matches))
    gwport_matches = list(set(gwport_matches))
    swport_matches = list(set(swport_matches))

    if request.REQUEST.get('hide', False):
        for gwport in gwport_matches:
            if not gwport.ifalias:
                gwport_matches.remove(gwport)
        for swport in swport_matches:
            if not swport.ifalias:
                swport_matches.remove(swport)

    # Get the html up-front
    routers = []
    for router in router_matches:
        req = HttpRequest()
        req.GET['netboxid'] = router.id
        routers.append([router.id, expand_router(req).content])

    gwports = []
    for gwport in gwport_matches:
        req = HttpRequest()
        req.GET['gwportid'] = gwport.id
        gwports.append([gwport.id, expand_gwport(req).content])

    swports = []
    for swport in swport_matches:
        req = HttpRequest()
        req.GET['swportid'] = swport.id
        swports.append([swport.id, expand_swport(req).content])

    return HttpResponse(simplejson.dumps({'routers': routers, 'gwports': gwports, 'swports': swports}))

class FakeRequest:
    """Simple class for faking requests"""
    def __init__(self, request):
        self.REQUEST = {}
        self.GET = {}
        self.POST = {}

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

from django.core import serializers
from django.core import serializers
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect, HttpResponseBadRequest, Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response as render_to_response_orig
from django.template import Context, Template
from django.template import RequestContext
from django.utils import simplejson
from django.db.models import Q

from nav.django.shortcuts import render_to_response, object_list
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, Module, SwPort, GwPort
from nav.models.service import Service

from nav.web.templates.NetworkExplorerTemplate import NetworkExplorerTemplate

import nav.natsort

def index(request):
    """Basic view of the network"""

    routers = Netbox.objects.all().filter(category__in=['GW', 'GSW'])
    for router in routers:
        if len(router.get_gwports()) > 0:
            router.has_children = True
    return render_to_response(NetworkExplorerTemplate, 'networkexplorer/base.html',
        {
            'routers': routers,
        }, context_instance=RequestContext(request))

def expand_router(request):
    """
    Returns children of an router according to spec
    """
    router = get_object_or_404(Netbox, id=request.REQUEST['netboxid'])
    gwports = router.get_gwports()
    interface_names = [p.interface for p in gwports]
    unsorted = dict(zip(interface_names, gwports))
    interface_names.sort(key=nav.natsort.split)
    sorted_ports = [unsorted[i] for i in interface_names]

    for gwport in sorted_ports:
        # Check if the port is expandable
        for prefix in gwport.gwportprefix_set.all():
            if prefix.prefix.vlan.swportvlan_set.all().count() > 0:
                gwport.has_children = True
                break
        if gwport.to_netbox:
            continue
        if gwport.to_swport and gwport.to_swport.module.netbox:
            gwport.to_netbox = gwport.to_swport.module.netbox
            continue
        # Find connection trough prefixes
        try:
            for gwprefix in gwport.gwportprefix_set.all():
                for prefix in prefix.gwportprefix_set.all().exclude(gwport=gwport):
                    gwport.to_netbox = prefix.gwport.module.netbox
                    raise StopIteration # Ugly hack since python doesnt support labeled breaks
        except:
            continue

    return render_to_response_orig('networkexplorer/expand_router.html',
        {
            'sysname': router.sysname,
            'ports': sorted_ports,
        })

def expand_gwport(request):
    """
    """
    gwport = get_object_or_404(GwPort, id=request.REQUEST['gwportid'])
    vlans = []
    foreign_netboxes = []
    prefixes = gwport.gwportprefix_set.all().select_related()
    for prefix in prefixes:
        for vlan in prefix.prefix.vlan.swportvlan_set.all().select_related()\
            .filter(swport__module__netbox=gwport.module.netbox).order_by('swport__interface'):
            if not vlan in vlans:
                if vlan.swport.to_netbox and vlan.swport.to_netbox.service_set.all().count() > 0:
                    vlan.swport.has_children = True
                if vlan.swport.to_swport and vlan.swport.to_swport.module.netbox.service_set.all().count() > 0:
                    vlan.swport.has_children = True
                vlans.append(vlan)
                foreign_netboxes.append(vlan.swport.module.netbox)

    return render_to_response_orig('networkexplorer/expand_gwport.html',
        {
            'gwport': gwport,
            'vlans': vlans,
        }, context_instance=RequestContext(request))

def expand_swport(request):
    """
    """
    swport = get_object_or_404(SwPort, id=request.REQUEST['swportid'])
    if swport.to_netbox:
        to_netbox = swport.to_netbox
    else:
        to_netbox = swport.to_swport.module.netbox

    return render_to_response_orig('networkexplorer/expand_swport_server.html',
        {
            'netbox': to_netbox,
            'services': to_netbox.service_set.all(),
        })

def search(request):
    """
    """
    # Raise 404 if no parameters are given
    if 'lookup_field' not in request.REQUEST:
        raise Http404

    router_matches = []
    gwport_matches = []
    swport_matches = []


    # Sysname-search
    if request.REQUEST['lookup_field'] == 'sysname':
        routers = Netbox.objects.all().filter(sysname__icontains=request.REQUEST['lookup_field'], category__in=['GW','GSW'])
        netboxes = Netbox.objects.all().filter(sysname__icontains=request.REQUEST['lookup_field'])

        for router in routers:
            router_matches.append(router.id)

        for gwport in GwPort.objects.all().filter(module__netbox__in=netboxes):
            gwport_matches.append(gwport.id)

        local_swports = SwPort.objects.all().filter(module__netbox__in=netboxes)
        for swport in local_swports:
            swport_matches.append(swport.id)

        gwports = GwPort.objects.all().filter(
            Q(to_netbox__in=netboxes) |
            Q(to_swport__module__netbox__in=routers))
        for gwport in gwports:
            router_matches.append(gwport.module.netbox.id)
            gwport_matches.append(gwport.id)

        swports = SwPort.objects.all().filter(
            Q(to_netbox__in=netboxes) |
            Q(to_swport__in=local_swports))
        for swport in swports:
            router_matches.append(swport.module.netbox.id)
            swport_matches.append(swport.id)
            # Find path from swport to gwport (and the router)
            for swportvlan in swport.swportvlan_set.all():
                for prefix in swportvlan.vlan.prefix_set.all():
                    for gwportprefix in prefix.gwportprefix_set.all():
                        gwport_matches.append(gwportprefix.gwport.id)
                        router_matches.append(gwportprefix.gwport.module.netbox.id)

    # A bit ugly hack to remove duplicates, but simplejson doesnt seem to support sets
    router_matches = list(set(router_matches))
    gwport_matches = list(set(gwport_matches))
    swport_matches = list(set(swport_matches))
    return HttpResponse(simplejson.dumps({'routers': router_matches, 'gwports': gwport_matches, 'swports': swport_matches}))

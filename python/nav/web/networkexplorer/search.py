#
# Copyright (C) 2007-2008 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import re
import datetime

from django.db.models import Q

from nav.models.manage import Netbox, Cam, Arp, GwPortPrefix
from nav.models.manage import SwPortVlan, Interface, Prefix


MacRE = re.compile(r'^([a-fA-F0-9]{2}[:|\-]?){6}$')


def search(data):
    exact_results = data.get('exact_results', False)
    hide_ports = data.get('hide_ports', False)
    query = data['query'][0]
    query_type = data['query'][1]
    search_function = None

    if query_type == 'sysname':
        search_function = sysname_search
    elif query_type == 'ip':
        search_function = ip_search
    elif query_type == 'mac':
        search_function = mac_search
    elif query_type == 'room':
        search_function = room_search
    elif query_type == 'vlan':
        search_function = vlan_search
    elif query_type == 'port':
        search_function = portname_search

    (
        router_matches,
        qwport_matches,
        swport_matches,
    ) = search_function(query, exact_results)

    if hide_ports:
        hide_gwports = set()
        hide_swports = set()
        for gwport in qwport_matches:
            if not gwport.ifalias:
                hide_gwports.add(gwport)
        for swport in swport_matches:
            if not swport.ifalias:
                hide_swports.add(swport)

        qwport_matches -= hide_gwports
        swport_matches -= hide_swports

    return {
        # Ensure list for JSON-serialization
        'routers': [router.pk for router in router_matches],
        'gwports': [gwport.pk for gwport in qwport_matches],
        'swports': [swport.pk for swport in swport_matches],
    }


def search_expand_swport(swportid=None, swport=None, scanned=[]):
    """
    Expands all paths to a switch port
    """
    if not swport:
        try:
            swport = Interface.objects.get(id=swportid)
        except Interface.DoesNotExist:
            return [], []

    found_swports = []
    found_gwports = []

    # Find gwport that has the same vlan
    for swportvlan in swport.swport_vlans.exclude(
        vlan__net_type='static'
    ).select_related():
        for prefix in swportvlan.vlan.prefixes.all():
            for gwportprefix in prefix.gwport_prefixes.all():
                found_gwports.append(gwportprefix.interface)

    for port in (
        Interface.objects.filter(to_interface=swport)
        .exclude(to_interface__in=scanned)
        .select_related()
    ):
        scanned.append(port)

        found_swports.append(port)

        recurs_found = search_expand_swport(swport=port, scanned=scanned)
        found_gwports.extend(recurs_found[0])
        found_swports.extend(recurs_found[1])

    for port in Interface.objects.filter(
        to_interface__in=found_swports, gwport_prefixes__isnull=False
    ):
        found_gwports.append(port)

    for port in Interface.objects.filter(
        to_netbox=swport.netbox, gwport_prefixes__isnull=False
    ):
        found_gwports.append(port)

    for port in Interface.objects.filter(
        to_interface=swport, gwport_prefixes__isnull=False
    ):
        found_gwports.append(port)

    return found_gwports, found_swports


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
            return [], []

    for result in netbox.get_uplinks():
        if (
            result['other'].__class__ == Interface
            and result['other'].gwport_prefixes.count()
        ):
            found_gwports.append(result['other'])
        else:
            found_swports.append(result['other'])

    ports = Interface.objects.filter(to_netbox=netbox)
    gwports = ports.filter(gwport_prefixes__isnull=False)
    swports = ports.filter(baseport__isnull=False)

    found_gwports.extend(gwports)

    for swport in swports:
        found_swports.append(swport)
        ses = search_expand_swport(swport=swport)
        found_gwports.extend(ses[0])
        found_swports.extend(ses[1])

    return found_gwports, found_swports


def search_expand_sysname(sysname=None):
    """ """
    try:
        netbox = Netbox.objects.get(sysname=sysname)
    except Netbox.DoesNotExist:
        return [], []

    return search_expand_netbox(netbox=netbox)


def search_expand_mac(mac=None):
    """ """

    if not mac or not MacRE.match(mac):
        return [], []

    found_swports = []
    found_gwports = []

    cam_entries = Cam.objects.filter(
        mac=mac,
        end_time__gte=datetime.datetime.max,
    ).select_related()

    for cam_entry in cam_entries:
        for swport in Interface.objects.filter(
            netbox=cam_entry.netbox,
            ifname=cam_entry.port,
        ).select_related():
            found_swports.append(swport)
            swport_search = search_expand_swport(swport=swport)
            found_gwports.extend(swport_search[0])
            found_swports.extend(swport_search[1])

    return found_gwports, found_swports


# Search functions


def sysname_search(sysname, exact=False):
    """
    Searches the database for any connections to the sysname
    """
    router_matches = set()
    gwport_matches = set()
    swport_matches = set()

    if exact:
        routers = Netbox.objects.filter(sysname=sysname, category__in=['GW', 'GSW'])
        netboxes = Netbox.objects.filter(sysname=sysname)
    else:
        routers = Netbox.objects.filter(
            sysname__icontains=sysname, category__in=['GW', 'GSW']
        )
        netboxes = Netbox.objects.filter(sysname__icontains=sysname)

    for router in routers:
        router_matches.add(router)

    for netbox in netboxes:
        netbox_search = search_expand_netbox(netbox=netbox)
        gwport_matches.update(netbox_search[0])
        swport_matches.update(netbox_search[1])

    interfaces = Interface.objects.filter(module__netbox__in=netboxes)

    for gwport in interfaces.filter(gwport_prefixes__isnull=False):
        gwport_matches.add(gwport)

    for swport in interfaces.filter(baseport__isnull=False):
        swport_matches.add(swport)
        swport_search = search_expand_swport(swport=swport)
        gwport_matches.update(swport_search[0])
        swport_matches.update(swport_search[1])

    router_matches.update([gwport.netbox for gwport in gwport_matches])

    return router_matches, gwport_matches, swport_matches


def ip_search(ip, exact=False):
    """
    Searches the database for anything related to the ip

    Returns a list of (routers, gwports, swports)
    """
    router_matches = set()
    gwport_matches = set()
    swport_matches = set()

    if exact:
        netboxes = Netbox.objects.filter(ip=ip)
        gwportprefixes = GwPortPrefix.objects.filter(gw_ip=ip)
        arp_entries = Arp.objects.filter(ip=ip, end_time__gte=datetime.datetime.max)
    else:
        netboxes = Netbox.objects.filter(ip__contains=ip)
        gwportprefixes = GwPortPrefix.objects.filter(gw_ip__contains=ip)
        arp_entries = Arp.objects.filter(
            ip__contains=ip, end_time__gte=datetime.datetime.max
        )

    # Add matching routers
    router_matches.update(
        [netbox for netbox in netboxes.filter(category__in=['GW', 'GSW'])]
    )

    for netbox in netboxes:
        netbox_search = search_expand_netbox(netbox=netbox)
        gwport_matches.update(netbox_search[0])
        swport_matches.update(netbox_search[1])

    for prefix in gwportprefixes:
        gwport_matches.add(prefix.interface)

    for arp_entry in arp_entries:
        mac_search = search_expand_mac(mac=arp_entry.mac)
        gwport_matches.update(mac_search[0])
        swport_matches.update(mac_search[1])

    router_matches.update([gwport.netbox for gwport in gwport_matches])

    return router_matches, gwport_matches, swport_matches


def portname_search(portname, exact=False):
    """ """
    router_matches = set()
    gwport_matches = set()
    swport_matches = set()

    interfaces = Interface.objects.filter(baseport__isnull=False)
    if exact:
        swport_matches.update(interfaces.filter(ifalias=portname))
    else:
        swport_matches.update(interfaces.filter(ifalias__icontains=portname))

    for swport in [swport for swport in swport_matches if swport]:
        swport_search = search_expand_swport(swport=swport)
        gwport_matches.update(swport_search[0])
        swport_matches.update(swport_search[1])

    router_matches.update([gwport.netbox for gwport in gwport_matches])

    return router_matches, gwport_matches, swport_matches


def room_search(room, exact=False):
    """ """
    router_matches = set()
    gwport_matches = set()
    swport_matches = set()

    interfaces = Interface.objects.filter(baseport__isnull=False)
    if exact:
        swport_matches.update(interfaces.filter(netbox__room__id=room))
    else:
        swport_matches.update(interfaces.filter(netbox__room__id__icontains=room))

    for swport in [swport for swport in swport_matches if swport]:
        swport_search = search_expand_swport(swport=swport)
        gwport_matches.update(swport_search[0])
        swport_matches.update(swport_search[1])

    router_matches.update([gwport.netbox for gwport in gwport_matches])

    return router_matches, gwport_matches, swport_matches


def mac_search(mac, exact=False):
    """ """
    search = search_expand_mac(mac)
    gwport_matches = set(search[0])
    swport_matches = set(search[1])
    router_matches = {gwport.netbox for gwport in gwport_matches}

    return router_matches, gwport_matches, swport_matches


def vlan_search(vlan, exact=False):
    """ """
    router_matches = set()
    gwport_matches = set()
    swport_matches = set()

    if exact:
        vlan_filter = Q(vlan__vlan=vlan)
    else:
        vlan_filter = Q(vlan__vlan__icontains=vlan)

    for swportvlan in SwPortVlan.objects.filter(vlan_filter):
        swport_search = search_expand_swport(swport=swportvlan.interface)
        gwport_matches.update(swport_search[0])
        swport_matches.update(swport_search[1])

    matching_prefixes = Prefix.objects.filter(vlan_filter).exclude(
        vlan__net_type='static'
    )

    for gwportprefix in GwPortPrefix.objects.filter(prefix__in=matching_prefixes):
        gwport_matches.add(gwportprefix.interface)

    for netbox in Netbox.objects.filter(netboxprefix__prefix__in=matching_prefixes):
        netbox_search = search_expand_netbox(netbox=netbox)
        gwport_matches.update(netbox_search[0])
        swport_matches.update(netbox_search[1])

    router_matches.update([gwport.netbox for gwport in gwport_matches])

    return router_matches, gwport_matches, swport_matches

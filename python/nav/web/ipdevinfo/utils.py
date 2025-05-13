#
# Copyright (C) 2008, 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Utility methods to get extract extra characteristics from ports."""

import logging
from datetime import datetime
from operator import attrgetter

import networkx as nx

from django.core.validators import validate_email, ValidationError

from nav.models.manage import SwPortVlan, SwPortBlocked, Cam
from nav.models.manage import Netbox
from nav.topology.vlan import build_layer2_graph

from nav.metrics.graphs import get_metric_meta, get_simple_graph_url
from nav.metrics.templates import metric_path_for_interface
import nav.util

_logger = logging.getLogger('nav.web.ipdevinfo.utils')


def get_module_view(module_object, perspective, activity_interval=None, netbox=None):
    """
    Returns a dict structure of ports on the module with additional meta
    information.

    Arguments:
    perspective -- string that decides what kind of ports are included, can be
        either ''swportstatus'', ''swportactive'', or ''gwportstatus''.

    Keyword arguments:
    activity_interval -- the number of days to check for port activity if
        perspective is ''swportactive''.

    """

    assert perspective in (
        'swportstatus',
        'swportactive',
        'gwportstatus',
        'physportstatus',
    )

    module = {
        'object': module_object,
        'ports': [],
    }

    ports = None
    if perspective in ('swportstatus', 'swportactive'):
        if not module_object and netbox:
            ports = [p for p in netbox.get_swports_sorted() if not p.module]
        else:
            ports = module_object.get_swports_sorted()
    elif perspective == 'gwportstatus':
        if not module_object and netbox:
            ports = [p for p in netbox.get_gwports_sorted() if not p.module]
        else:
            ports = module_object.get_gwports_sorted()
    elif perspective == 'physportstatus':
        if not module_object and netbox:
            ports = [p for p in netbox.get_physical_ports_sorted() if not p.module]
        else:
            ports = module_object.get_physical_ports_sorted()

    if ports:
        _cache_vlan_data_in_ports(ports)
        for port_object in ports:
            port = {'object': port_object}

            if perspective in ('swportstatus', 'physportstatus'):
                port['class'] = _get_swportstatus_class(port_object)
                port['style'] = ''
                port['title'] = _get_swportstatus_title(port_object)
            elif perspective == 'swportactive':
                port['class'] = _get_swportactive_class(port_object, activity_interval)
                port['style'] = _get_swportactive_style(port_object, activity_interval)
                port['title'] = _get_swportactive_title(port_object, activity_interval)
            elif perspective == 'gwportstatus':
                port['class'] = _get_gwportstatus_class(port_object)
                port['style'] = ''
                port['title'] = _get_gwportstatus_title(port_object)

            if perspective == 'physportstatus':
                # Add extra class to differentiate between layers.
                if port_object.is_gwport():
                    port['oplayer'] = '3'
                elif port_object.is_swport():
                    port['oplayer'] = '2'

            module['ports'].append(port)

    return module


def _cache_vlan_data_in_ports(ports):
    """Loads and caches vlan data associated with an Interface queryset.

    The caches are kept within each Interface object from the ports
    queryset, and can be used to avoid multiple subqueries when
    processing multiple Interfaces at once.

    """
    swpvlans = SwPortVlan.objects.filter(interface__in=ports).select_related('vlan')
    blocked_vlans = SwPortBlocked.objects.filter(interface__in=ports)

    for port in ports:
        port._vlan_cache = set(
            swpvlan.vlan.vlan for swpvlan in swpvlans if swpvlan.interface == port
        )
        if port.vlan is not None:
            port._vlan_cache.add(port.vlan)

        port._blocked_vlans_cache = set(
            blocked_vlan.vlan
            for blocked_vlan in blocked_vlans
            if blocked_vlan.interface == port
        )


def _get_swportstatus_class(swport):
    """Classes for the swportstatus port view"""

    classes = ['port']
    if swport.ifoperstatus == swport.OPER_UP and swport.speed:
        classes.append('Mb%d' % swport.speed)
    if swport.ifadminstatus == swport.ADM_DOWN:
        classes.append('disabled')
    elif swport.ifoperstatus != swport.OPER_UP:
        classes.append('passive')
    if swport.trunk:
        classes.append('trunk')
    if swport.duplex:
        classes.append('%sduplex' % swport.duplex)
    if swport._blocked_vlans_cache:
        classes.append('blocked')
    return ' '.join(classes)


def _get_swportstatus_title(swport):
    """Title for the swportstatus port view"""

    title = []

    if swport.ifname:
        title.append(swport.ifname)

    if swport.ifoperstatus == swport.OPER_UP and swport.speed:
        title.append('%d Mbit' % swport.speed)
    elif swport.ifadminstatus == swport.ADM_DOWN:
        title.append('disabled')
    elif swport.ifoperstatus != swport.OPER_UP:
        title.append('not active')

    if swport.duplex:
        title.append(swport.get_duplex_display())

    vlan_numbers = _get_vlan_numbers(swport)
    if vlan_numbers:
        title.append('vlan ' + ','.join(map(str, vlan_numbers)))

    if swport.trunk:
        title.append('trunk')

    if swport.ifalias:
        title.append('"%s"' % swport.ifalias)

    try:
        if swport.to_netbox:
            title.append('-> %s' % swport.to_netbox)
    except Netbox.DoesNotExist:
        pass

    if swport._blocked_vlans_cache:
        title.append('blocked ' + ','.join(str(b) for b in swport._blocked_vlans_cache))

    return ', '.join(title)


def _get_vlan_numbers(swport):
    """Returns active vlans on an swport, using cached data, if available."""
    if hasattr(swport, '_vlan_cache'):
        return swport._vlan_cache
    else:
        return swport.get_vlan_numbers()


def _get_swportactive_class(swport, interval=30):
    """Classes for the swportactive port view"""

    classes = ['port']

    if swport.ifoperstatus == swport.OPER_UP:
        classes.append('active')
        classes.append('link')
    else:
        active = swport.get_active_time(interval)
        if active is not None:
            classes.append('active')
        else:
            classes.append('inactive')

    return ' '.join(classes)


def _get_swportactive_style(swport, interval=30):
    """Style for the swportactive port view"""

    # Color range for port activity
    color_recent = (116, 196, 118)
    color_longago = (229, 245, 224)
    # XXX: Is this CPU intensive? Cache result?
    gradient = nav.util.color_gradient(color_recent, color_longago, interval)

    style = ''

    if swport.ifoperstatus == swport.OPER_UP:
        style = 'background-color: #%s;' % nav.util.colortohex(gradient[0])
    else:
        active = swport.get_active_time(interval)
        if active is not None:
            style = 'background-color: #%s;' % nav.util.colortohex(
                gradient[active.days]
            )

    return style


def _get_swportactive_title(swport, interval=30):
    """Title for the swportactive port view"""

    title = []

    if swport.ifname:
        title.append(swport.ifname)

    if swport.ifoperstatus == swport.OPER_UP:
        title.append('link now')
    else:
        active = swport.get_active_time(interval)
        if active is not None:
            if active.days > 1:
                title.append('MAC seen %d days ago' % active.days)
            elif active.days == 1:
                title.append('MAC seen 1 day ago')
            else:
                title.append('MAC seen today')
        else:
            title.append('free')

    if swport.ifalias:
        title.append('"%s"' % swport.ifalias)

    return ', '.join(title)


def _get_gwportstatus_class(gwport):
    """Classes for the gwportstatus port view"""

    classes = ['port']
    if gwport.speed:
        classes.append('Mb%d' % gwport.speed)
    return ' '.join(classes)


def _get_gwportstatus_title(gwport):
    """Title for the gwportstatus port view"""

    title = []

    if gwport.ifname:
        title.append(gwport.ifname)

    if gwport.speed:
        title.append('%d Mbit' % gwport.speed)

    if gwport.ifalias:
        title.append('"%s"' % gwport.ifalias)

    try:
        if gwport.to_netbox:
            title.append('-> %s' % gwport.to_netbox)
    except Netbox.DoesNotExist:
        pass

    return ', '.join(title)


def find_children(netbox, netboxes=None):
    """Recursively find all children from this netbox"""
    if not netboxes:
        netboxes = [netbox]

    interfaces = netbox.interfaces.filter(
        to_netbox__isnull=False, swport_vlans__direction=SwPortVlan.DIRECTION_DOWN
    )
    for interface in interfaces:
        if interface.to_netbox not in netboxes:
            netboxes.append(interface.to_netbox)
            find_children(interface.to_netbox, netboxes)

    return netboxes


def find_organizations(netboxes):
    """Find all contact addresses for the netboxes"""
    return set(find_vlan_organizations(netboxes)) | set(
        find_netbox_organizations(netboxes)
    )


def find_netbox_organizations(netboxes):
    """Find direct contacts for the netboxes"""
    return [n.organization for n in netboxes if n.organization]


def find_vlan_organizations(netboxes):
    """Find contacts for the vlans on the downlinks on the netboxes"""
    vlans = []
    for netbox in netboxes:
        interfaces = netbox.interfaces.filter(
            to_netbox__isnull=False,
            swport_vlans__direction=SwPortVlan.DIRECTION_DOWN,
            swport_vlans__vlan__organization__isnull=False,
        )
        for interface in interfaces:
            vlans.extend(
                [v.vlan for v in interface.swport_vlans.exclude(vlan__in=vlans)]
            )

    return [v.organization for v in set(vlans) if v.organization]


def filter_email(organizations):
    """Filter the list of addresses to make sure it's an email-address"""
    valid_emails = []
    for organization in organizations:
        try:
            validate_email(organization.contact)
        except ValidationError:
            for extracted_email in organization.extract_emails():
                try:
                    validate_email(extracted_email)
                except ValidationError:
                    continue
                else:
                    valid_emails.append(extracted_email)
        else:
            valid_emails.append(organization.contact)

    return list(set(valid_emails))


def get_affected_host_count(netboxes):
    """Return the total number of active hosts on the netboxes"""
    return Cam.objects.filter(netbox__in=netboxes, end_time__gte=datetime.max).count()


def find_affected_but_not_down(netbox_going_down, netboxes):
    """Mark affected but not down because of redundancy boxes"""
    graph = build_layer2_graph()
    if not graph.has_node(netbox_going_down):
        return [netbox_going_down]
    graph.remove_node(netbox_going_down)
    masters = find_uplink_nodes(netbox_going_down)
    redundant = []
    for netbox in netboxes:
        if netbox_going_down == netbox:
            continue
        if any(nx.has_path(graph, master, netbox) for master in masters):
            redundant.append(netbox)

    return redundant


def find_uplink_nodes(netbox):
    """Find the uplink nodes for this netbox"""
    uplink_nodes = [x['other'].netbox for x in netbox.get_uplinks()]
    return list(set(uplink_nodes))


def sort_by_netbox(netboxes):
    """Sort netboxes by category and sysname"""
    return sorted(netboxes, key=attrgetter('category.id', 'sysname'))


def create_combined_urls(interface, counters):
    """Creates urls for displaying combined statistics for an interface"""
    return [
        get_interface_counter_graph_url(interface, kind=counter) for counter in counters
    ]


def get_interface_counter_graph_url(
    interface, timeframe='day', kind='Octets', expect='json'
):
    """Returns a Graphite graph render URL for an interface traffic graph"""

    def _get_target(direction):
        assert direction.lower() in ('in', 'out')
        path = metric_path_for_interface(
            interface.netbox.sysname,
            interface.ifname,
            'if{0}{1}'.format(direction.capitalize(), kind),
        )
        meta = get_metric_meta(path)
        return meta['target'], meta.get('unit', None)

    (out_series, unit), (in_series, unit) = [_get_target(d) for d in ('out', 'in')]

    in_series = 'alias({0},"In")'.format(in_series)
    out_series = 'alias({0},"Out")'.format(out_series)

    titlemap = dict(
        octets='Traffic on {shortname}:{ifname} {ifalias}',
        errors='Errors on {shortname}:{ifname} {ifalias}',
        ucastpkts='Unicast packets on {shortname}:{ifname}',
        multicastpkts='Multicast packets on {shortname}:{ifname}',
        broadcastpkts='Broadcast packets on {shortname}:{ifname}',
        discards='Discarded packets on {shortname}:{ifname}',
    )
    title = titlemap.get(kind.lower(), '{ifname}').format(
        ifname=interface.ifname,
        ifalias=("(%s)" % interface.ifalias) if interface.ifalias else '',
        sysname=interface.netbox.sysname,
        shortname=interface.netbox.get_short_sysname(),
    )

    return get_simple_graph_url(
        [in_series, out_series],
        "1" + timeframe,
        title=title,
        format=expect,
        vtitle=unit or '',
    )

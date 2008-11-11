# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

import nav.util

def get_module_view(module_object, perspective, activity_interval=None):
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

    assert perspective in ('swportstatus', 'swportactive', 'gwportstatus')

    module = {
        'object': module_object,
        'ports': [],
    }

    if perspective in ('swportstatus', 'swportactive'):
        ports = module_object.get_swports_sorted()
    elif perspective == 'gwportstatus':
        ports = module_object.get_gwports_sorted()

    for port_object in ports:
        port = {'object': port_object}

        if perspective == 'swportstatus':
            port['class'] = _get_swportstatus_class(port_object)
            port['style'] = ''
            port['title'] = _get_swportstatus_title(port_object)
        elif perspective == 'swportactive':
            port['class'] = _get_swportactive_class(
                port_object, activity_interval)
            port['style'] = _get_swportactive_style(
                port_object, activity_interval)
            port['title'] = _get_swportactive_title(
                port_object, activity_interval)
        elif perspective == 'gwportstatus':
            port['class'] = _get_gwportstatus_class(port_object)
            port['style'] = ''
            port['title'] = _get_gwportstatus_title(port_object)

        module['ports'].append(port)

    return module

def _get_swportstatus_class(swport):
    """Classes for the swportstatus port view"""

    classes = ['port']
    if swport.link == swport.LINK_UP and swport.speed:
        classes.append('Mb%d' % swport.speed)
    if swport.link == swport.LINK_DOWN_ADM:
        classes.append('disabled')
    elif swport.link != swport.LINK_UP:
        classes.append('passive')
    if swport.trunk:
        classes.append('trunk')
    if swport.duplex:
        classes.append('%sduplex' % swport.duplex)
    # XXX: This causes a DB query per port
    if swport.swportblocked_set.count():
        classes.append('blocked')
    return ' '.join(classes)

def _get_swportstatus_title(swport):
    """Title for the swportstatus port view"""

    title = []

    if swport.interface:
        title.append(swport.interface)

    if swport.link == swport.LINK_UP and swport.speed:
        title.append('%d Mbit' % swport.speed)
    elif swport.link == swport.LINK_DOWN_ADM:
        title.append('disabled')
    elif swport.link != swport.LINK_UP:
        title.append('not active')

    if swport.duplex:
        title.append(swport.get_duplex_display())

    if swport.get_vlan_numbers():
        title.append('vlan ' + ','.join(map(str, swport.get_vlan_numbers())))

    if swport.trunk:
        title.append('trunk')

    if swport.port_name:
        title.append('"%s"' % swport.port_name)

    try:
        if swport.to_netbox:
            title.append('-> %s' % swport.to_netbox)
    except Netbox.DoesNotExist:
        pass

    # XXX: This causes a DB query per port
    blocked_vlans = [str(block.vlan)
        for block in swport.swportblocked_set.select_related(depth=1)]
    if blocked_vlans:
        title.append('blocked ' + ','.join(blocked_vlans))

    return ', '.join(title)

def _get_swportactive_class(swport, interval=30):
    """Classes for the swportactive port view"""

    classes = ['port']

    if swport.link == swport.LINK_UP:
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

    if swport.link == swport.LINK_UP:
        style = 'background-color: #%s;' % nav.util.colortohex(
            gradient[0])
    else:
        active = swport.get_active_time(interval)
        if active is not None:
            style = 'background-color: #%s;' % nav.util.colortohex(
                gradient[active.days])

    return style

def _get_swportactive_title(swport, interval=30):
    """Title for the swportactive port view"""

    title = []

    if swport.interface:
        title.append(swport.interface)

    if swport.link == swport.LINK_UP:
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

    if swport.port_name:
        title.append('"%s"' % swport.port_name)

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

    if gwport.interface:
        title.append(gwport.interface)

    if gwport.speed:
        title.append('%d Mbit' % gwport.speed)

    if gwport.port_name:
        title.append('"%s"' % gwport.port_name)

    try:
        if gwport.to_netbox:
            title.append('-> %s' % gwport.to_netbox)
    except Netbox.DoesNotExist:
        pass

    return ', '.join(title)

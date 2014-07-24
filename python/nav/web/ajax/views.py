#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Ajax view definitions

The view definitions does not necessarily need to be placed here.
"""

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import simplejson

from nav.models.manage import Room, Netbox


def get_rooms_with_position(request, roomid=None):
    """
    Get rooms for presentation in OSM map
    """
    if roomid:
        rooms = Room.objects.filter(id=roomid,position__isnull=False)
    else:
        rooms = Room.objects.filter(position__isnull=False)
    data = {'rooms': []}
    for room in rooms:
        roomdata = {
            'name': room.id,
            'position': ",".join([str(pos) for pos in room.position]),
            'status': get_room_status(room)
        }
        data['rooms'].append(roomdata)

    return HttpResponse(simplejson.dumps(data),
                        mimetype='application/json')


def get_room_status(room):
    """
    Return room status suitable for RoomMapper
    """
    return 'faulty' if netbox_down_in(room) else 'ok'


def netbox_down_in(room):
    """
    Returns True if a netbox is down on the room, otherwise False
    """
    return len(room.netbox_set.filter(up='n'))


def get_neighbors(request, netboxid):
    """Get neighbours for this netboxid

    Used in neighbour-map

    """

    nodes = []
    links = []
    link_candidates = {}

    netbox = get_object_or_404(Netbox, pk=netboxid)
    netboxes = [netbox]
    interfaces = netbox.interface_set.filter(to_netbox__isnull=False)
    for interface in interfaces:
        to_netbox = interface.to_netbox
        to_interfacename = (interface.to_interface.ifname
                            if interface.to_interface else '')
        if interface.to_netbox in link_candidates:
            link_candidates[to_netbox]['ifname'].append(
                interface.ifname)
            link_candidates[interface.to_netbox]['to_ifname'].append(
                to_interfacename)
        else:
            netboxes.append(interface.to_netbox)
            link_candidates[interface.to_netbox] = {
                "sourceId": netbox.id,
                "targetId": to_netbox.id,
                "ifname": [interface.ifname],
                "to_ifname": [to_interfacename]}

    for i in link_candidates.values():
        links.append(i)

    for n in netboxes:
        nodes.append({"netboxid": n.id,
                      "name": n.get_short_sysname(),
                      "sysname": n.sysname,
                      "category": n.category.id})

    # Unrecognized neighbours
    unrecognized_nodes = []
    un_candidates = {}
    for unrecognized in netbox.unrecognizedneighbor_set.all():
        if unrecognized.remote_id in un_candidates:
            un_candidates[unrecognized.remote_id]['ifname'].append(
                unrecognized.interface.ifname)
        else:
            unrecognized_nodes.append(unrecognized)
            un_candidates[unrecognized.remote_id] = {
                "sourceId": netbox.id,
                "targetId": unrecognized.remote_id,
                "ifname": [unrecognized.interface.ifname],
                "to_ifname": ""
            }

    for i in un_candidates.values():
        links.append(i)

    for u in unrecognized_nodes:
        nodes.append({
            "netboxid": u.remote_id,
            "name": u.remote_name,
            "sysname": u.remote_name,
            "category": 'UNRECOGNIZED'
        })

    data = {
        "nodes": nodes,
        "links": links
    }

    return HttpResponse(simplejson.dumps(data), mimetype="application/json")



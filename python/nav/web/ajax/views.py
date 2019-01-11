#
# Copyright (C) 2012 Uninett AS
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
"""
Ajax view definitions

The view definitions does not necessarily need to be placed here.
"""

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from nav.models.manage import Room, Netbox, Location


def _process_room_position(rooms):
    data = {'rooms': []}
    for room in rooms:
        roomdata = {
            'name': room.id,
            'position': ",".join([str(pos) for pos in room.position]),
            'status': get_room_status(room)
        }
        data['rooms'].append(roomdata)

    return JsonResponse(data)


def get_rooms_with_position(_request, roomid=None):
    """
    Get rooms for presentation in OSM map
    """
    if roomid:
        rooms = Room.objects.filter(id=roomid, position__isnull=False)
    else:
        rooms = Room.objects.filter(position__isnull=False)
    return _process_room_position(rooms)


def get_rooms_with_position_for_location(_request, locationid):
    """
    Get rooms for presentation in OSM map based on location
    """
    location = Location.objects.get(pk=locationid)
    rooms = location.get_all_rooms().filter(position__isnull=False)
    return _process_room_position(rooms)


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


def get_neighbors(_request, netboxid):
    """Get neighbors for this netboxid

    Used in neighbor-map

    """

    link_candidates = {}

    netbox = get_object_or_404(Netbox, pk=netboxid)
    nodes = [create_object_from(netbox)]
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
            nodes.append(create_object_from(interface.to_netbox))
            link_candidates[interface.to_netbox] = {
                "source": netbox.id,
                "target": to_netbox.id,
                "ifname": [interface.ifname],
                "to_ifname": [to_interfacename]}

    # Unrecognized neighbors
    unrecognized_nodes = []
    un_candidates = {}
    for unrecognized in netbox.unrecognizedneighbor_set.filter(
            ignored_since__isnull=True):
        if unrecognized.remote_id in un_candidates:
            un_candidates[unrecognized.remote_id]['ifname'].append(
                unrecognized.interface.ifname)
        else:
            nodes.append(create_unrecognized_object_from(unrecognized))
            unrecognized_nodes.append(unrecognized)
            un_candidates[unrecognized.remote_id] = {
                "source": netbox.id,
                "target": unrecognized.remote_id,
                "ifname": [unrecognized.interface.ifname],
                "to_ifname": ""
            }

    data = {
        "nodes": nodes,
        "links": link_candidates.values() + un_candidates.values()
    }

    return JsonResponse(data)


def create_object_from(netbox):
    """Create dict structure from netbox instance"""
    return {
        "netboxid": netbox.id,
        "name": netbox.get_short_sysname(),
        "sysname": netbox.sysname,
        "category": netbox.category.id
    }


def create_unrecognized_object_from(node):
    """Create dict structure from unrecognized neighbor instance"""
    return {
        "netboxid": node.remote_id,
        "name": node.remote_name,
        "sysname": node.remote_name,
        "category": 'UNRECOGNIZED'
    }

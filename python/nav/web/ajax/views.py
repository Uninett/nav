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


def get_neighbours(request, netboxid):
    """Get neighbours for this netboxid

    Used in neighbour-map

    """

    nodes = []
    links = []

    netbox = Netbox.objects.get(pk=netboxid)
    netboxes = [netbox]
    interfaces = netbox.interface_set.filter(to_netbox__isnull=False)
    for interface in interfaces:
        netboxes.append(interface.to_netbox)
        links.append({"sourceId": netbox.id,
                      "targetId": interface.to_netbox.id})

    netboxes = set(netboxes)
    for n in netboxes:
        nodes.append({"netboxid": n.id,
                      "name": n.get_short_sysname(),
                      "sysname": n.sysname,
                      "category": n.category.id})

    data = {
        "nodes": nodes,
        "links": links
    }

    return HttpResponse(simplejson.dumps(data), mimetype="application/json")



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

from nav.models.manage import Room


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





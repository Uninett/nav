#
# Copyright (C) 2016 UNINETT AS
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
"""Module containing RoomStatus"""

from datetime import datetime

from nav.models.event import AlertHistory
from nav.models.fields import INFINITY
from nav.models.manage import Room
from . import Navlet


class RoomStatus(Navlet):
    """Widget displaying status for rooms"""

    title = 'Rooms with active alerts'
    description = 'Displays a list of rooms with active alerts'
    refresh_interval = 30000  # 30 seconds

    def get_template_basename(self):
        return 'roomstatus'

    def get_context_data_view(self, context):
        rooms = Room.objects.filter(
            netbox__alerthistory__end_time__gte=INFINITY).distinct('id')
        for room in rooms:
            room.alerts = AlertHistory.objects.filter(
                netbox__room=room,
                end_time__gte=INFINITY).order_by('start_time')
            for alert in room.alerts:
                alert.sms_message = alert.messages.get(type='sms',
                                                       language='en')

        context['rooms'] = rooms
        context['last_update'] = datetime.now()
        return context

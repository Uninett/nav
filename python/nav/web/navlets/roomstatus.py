#
# Copyright (C) 2016 Uninett AS
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
"""Module containing RoomStatus"""

from datetime import datetime
from django import forms
from itertools import groupby
from operator import attrgetter

from nav.models.event import AlertHistory, STATE_START

from nav.web.navlets.status2 import Status2Widget


class RoomStatus(Status2Widget):
    """Widget displaying status for rooms"""

    title = 'Rooms with active alerts'
    description = 'Displays a list of rooms with active alerts'
    refresh_interval = 30000  # 30 seconds
    is_title_editable = True

    def get_template_basename(self):
        return 'room_location_status'

    def get_context_data_view(self, context):
        context = super(RoomStatus, self).get_context_data_view(context)
        assert 'results' in context

        result_ids = [r.get('id') for r in context['results']]
        alerts = AlertHistory.objects.filter(
            pk__in=result_ids).exclude(netbox__isnull=True).order_by(
            'netbox__room')
        rooms = []
        for room, alertlist in groupby(alerts, attrgetter('netbox.room')):
            room.alerts = sorted(alertlist, key=attrgetter('start_time'))
            for alert in room.alerts:
                alert.sms_message = alert.messages.get(
                    type='sms', language='en', state=STATE_START)
            rooms.append(room)

        context['items'] = rooms
        context['last_update'] = datetime.now()
        context['name'] = 'room'
        context['name_plural'] = 'rooms'
        context['history_route'] = 'devicehistory-view-room'
        context['info_route'] = 'room-info'
        return context

    def get_context_data_edit(self, context):
        context = super(RoomStatus, self).get_context_data_edit(context)
        context['form'].fields['extra_columns'].widget = forms.MultipleHiddenInput()
        return context

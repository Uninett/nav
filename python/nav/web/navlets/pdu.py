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
"""Module containing PDUWidget"""

from django.db.models import Q
from nav.metrics.graphs import get_simple_graph_url
from nav.models.manage import Room
from . import Navlet, NAVLET_MODE_EDIT
from .forms import PduWidgetForm

class PduWidget(Navlet):
    """Widget for displaying pdu overview for a room"""

    title = 'PDU load'
    is_editable = True
    is_title_editable = True
    ajax_reload = True
    description = 'Display PDU load for a room'
    refresh_interval = 30000  # 30 seconds

    def get_template_basename(self):
        return 'pdu'

    def get_context_data_edit(self, context):
        roomid = self.preferences.get('room_id')
        context['form'] = PduWidgetForm(self.preferences) if roomid else PduWidgetForm()
        return context

    def get_context_data_view(self, context):
        roomid = self.preferences.get('room_id')

        if roomid:
            room = Room.objects.get(pk=roomid)
            pdus = room.netbox_set.filter(category='POWER').filter(
                Q(sysname__startswith='pdu-') |
                Q(groups__in=['pdu'])).select_related('sensor')
            metrics = [s.get_metric_name() for pdu in pdus for s in pdu.sensor_set.all()]
            context['pdus'] = pdus
            context['data_url'] = get_simple_graph_url(
                metrics, time_frame='5 minutes', format='json', magic=False)
            context['room'] = room

        return context

    def post(self, request, **kwargs):
        """Save preferences"""
        form = PduWidgetForm(request.POST)
        return super(PduWidget, self).post(request, form=form)

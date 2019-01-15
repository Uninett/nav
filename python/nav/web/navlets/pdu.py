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
"""Module containing PDUWidget"""

from django.core.urlresolvers import reverse

from nav.models.manage import Room
import nav.natsort
from . import Navlet
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
        context['form'] = (PduWidgetForm(self.preferences)
                           if roomid else PduWidgetForm())
        return context

    def get_context_data_view(self, context):
        roomid = self.preferences.get('room_id')

        if not roomid:
            return context

        room = Room.objects.get(pk=roomid)
        pdus = room.netbox_set.filter(category='POWER').filter(
            sensor__internal_name__startswith='rPDULoadStatusLoad'
        ).select_related('sensor').distinct()
        sorted_pdus = sorted(pdus, key=lambda x: nav.natsort.split(x.sysname))
        metrics = [s.get_metric_name() for pdu in pdus
                   for s in pdu.sensor_set.filter(
                       internal_name__startswith='rPDULoadStatusLoad')]
        context['pdus'] = sorted_pdus
        context['metrics'] = metrics
        context['data_url'] = reverse('graphite-render')
        context['room'] = room

        return context

    def post(self, request, **kwargs):
        """Save preferences"""
        form = PduWidgetForm(request.POST)
        return super(PduWidget, self).post(request, form=form)

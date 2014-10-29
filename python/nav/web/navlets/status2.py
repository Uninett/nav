#
# Copyright (C) 2014 UNINETT AS
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
"""Status2 widget"""
import json
import logging

from django.http import HttpResponse, QueryDict

from nav.models.profiles import AccountNavlet
from nav.web.status2.forms import StatusWidgetForm
from . import Navlet, NAVLET_MODE_EDIT


class Status2Widget(Navlet):
    """Widget for displaying status"""

    title = "Status2"
    description = "Shows status for your ip-devices and services"
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes
    is_editable = True
    ajax_reload = True

    def get_template_basename(self):
        return "status2"

    def get_context_data(self, **kwargs):
        context = super(Status2Widget, self).get_context_data(**kwargs)
        navlet = AccountNavlet.objects.get(pk=self.navlet_id)
        status_filter = navlet.preferences.get('status_filter')
        context['path'] = status_filter
        if self.mode == NAVLET_MODE_EDIT:
            if status_filter:
                context['form'] = StatusWidgetForm(QueryDict(status_filter))
            else:
                context['form'] = StatusWidgetForm()
            context['interval'] = self.preferences['refresh_interval'] / 1000

        return context

    def post(self, request):
        try:
            navlet = AccountNavlet.objects.get(pk=self.navlet_id,
                                               account=request.account)
        except AccountNavlet.DoesNotExist:
            return HttpResponse(status=404)
        else:
            form = StatusWidgetForm(request.POST)
            if form.is_valid():
                navlet.preferences['status_filter'] = request.POST.urlencode()
                try:
                    navlet.preferences['refresh_interval'] = int(
                        request.POST['interval']) * 1000
                except Exception:
                    pass
                navlet.save()
                return HttpResponse(json.dumps(navlet.preferences))
            else:
                return HttpResponse(400)

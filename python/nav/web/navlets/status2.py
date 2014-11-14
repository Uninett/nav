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
from datetime import datetime
from operator import itemgetter

from django.http import HttpResponse, QueryDict
from django.test.client import RequestFactory

from nav.django.settings import DATETIME_FORMAT
from nav.models.profiles import AccountNavlet
from nav.web.status2.forms import StatusWidgetForm
from nav.web.status2.views import AlertHistoryViewSet
from . import Navlet, NAVLET_MODE_EDIT, NAVLET_MODE_VIEW


class Status2Widget(Navlet):
    """Widget for displaying status"""

    title = "Status2"
    description = "Shows status for your ip-devices and services"
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes
    is_editable = True
    is_title_editable = True

    def get_template_basename(self):
        return "status2"

    def get_context_data(self, **kwargs):
        context = super(Status2Widget, self).get_context_data(**kwargs)
        navlet = AccountNavlet.objects.get(pk=self.navlet_id)
        status_filter = navlet.preferences.get('status_filter')
        self.title = navlet.preferences.get('title', 'Status2')

        if self.mode == NAVLET_MODE_EDIT:
            if status_filter:
                context['form'] = StatusWidgetForm(QueryDict(status_filter))
            else:
                context['form'] = StatusWidgetForm()
            context['interval'] = self.preferences['refresh_interval'] / 1000
        elif self.mode == NAVLET_MODE_VIEW:
            results = self.do_query(status_filter)
            self.add_formatted_time(results)
            context['results'] = sorted(
                results, key=itemgetter('start_time'), reverse=True)
        context['last_updated'] = datetime.now()

        return context

    @staticmethod
    def do_query(query_string):
        """Queries for alerts given a query string"""
        factory = RequestFactory()
        view = AlertHistoryViewSet.as_view({'get': 'list'})
        request = factory.get("?%s" % query_string)
        response = view(request)
        return response.data.get('results')

    def add_formatted_time(self, results):
        """Adds formatted time to all results"""
        for result in results:
            result['formatted_time'] = self.format_time(result['start_time'])

    @staticmethod
    def format_time(timestamp):
        """Format the time based on time back in time"""
        now = datetime.now()
        date_format = '%d.%b %H:%M:%S'
        if now.year != timestamp.year:
            date_format = DATETIME_FORMAT
        elif now.date() == timestamp.date():
            date_format = '%H:%M:%S'
        return timestamp.strftime(date_format)

    def post(self, request):
        """Save navlet options on post"""
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

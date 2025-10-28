#
# Copyright (C) 2014 Uninett AS
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
"""Status2 widget"""

from datetime import datetime
from operator import itemgetter

from django.http import QueryDict, JsonResponse
from django.test.client import RequestFactory
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.dateparse import parse_datetime

from nav.models.profiles import Account
from nav.models.manage import Netbox
from nav.web.status2.forms import StatusWidgetForm
from nav.web.api.v1.views import AlertHistoryViewSet
from . import Navlet


class Status2Widget(Navlet):
    """Widget for displaying status"""

    title = "Status"
    description = "Shows status for your ip-devices and services"
    refresh_interval = 1000 * 60 * 10  # Refresh every 10 minutes
    is_editable = True
    is_title_editable = True

    def get_template_basename(self):
        return "status2"

    def get_context_data_view(self, context):
        self.title = self.preferences.get('title', self.title)
        status_filter = self.preferences.get('status_filter')
        results = self.do_query(status_filter)
        self.add_formatted_time(results)
        self.add_netbox(results)
        context['extra_columns'] = self.find_extra_columns(status_filter)
        context['results'] = sorted(results, key=itemgetter('start_time'), reverse=True)
        context['last_updated'] = datetime.now()
        return context

    def get_context_data_edit(self, context):
        self.title = self.preferences.get('title', self.title)
        status_filter = self.preferences.get('status_filter')
        if status_filter:
            context['form'] = StatusWidgetForm(QueryDict(str(status_filter)))
        else:
            context['form'] = StatusWidgetForm()
        context['interval'] = self.preferences['refresh_interval'] / 1000
        return context

    def do_query(self, query_string):
        """Queries for alerts given a query string"""
        factory = RequestFactory()
        view = AlertHistoryViewSet.as_view({'get': 'list'})
        request = factory.get("?%s" % query_string)
        account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
        # Fake request! This is safe
        # We cannot know whether the user is sudo'ed...
        # but since we operate as admin it is irrelevant
        request.account = request.user = account
        response = view(request)
        return response.data.get('results')

    def add_formatted_time(self, results):
        """Adds formatted time to all results"""
        for result in results:
            result['formatted_time'] = self.format_time(result['start_time'])

    @staticmethod
    def add_netbox(results):
        """Adds the netbox object to the result objects"""
        for result in results:
            try:
                netbox = Netbox.objects.select_related('room', 'room__location').get(
                    pk=int(result['netbox'])
                )
            except (Netbox.DoesNotExist, TypeError):
                pass
            else:
                result['netbox_object'] = netbox

    @staticmethod
    def find_extra_columns(status_filter):
        """Finds the chosen extra columns and returns them in a list"""
        column_choices = StatusWidgetForm().fields.get('extra_columns').choices
        chosen_columns = QueryDict(str(status_filter)).getlist('extra_columns')
        return [(k, v) for k, v in column_choices if k in chosen_columns]

    @staticmethod
    def format_time(timestampstring):
        """Format the time based on time back in time"""
        timestamp = parse_datetime(timestampstring)
        now = datetime.now()
        date_format = '%d.%b %H:%M:%S'
        if now.year != timestamp.year:
            date_format = '%Y-%m-%d %H:%M:%S'
        elif now.date() == timestamp.date():
            date_format = '%H:%M:%S'
        return timestamp.strftime(date_format)

    def post(self, request):
        """Save navlet options on post"""
        navlet = self.account_navlet
        form = StatusWidgetForm(request.POST)
        if form.is_valid():
            navlet.preferences['status_filter'] = request.POST.urlencode()
            try:
                navlet.preferences['refresh_interval'] = (
                    int(request.POST['interval']) * 1000
                )
            except (TypeError, ValueError, MultiValueDictKeyError):
                pass
            navlet.save()
            return JsonResponse(self.preferences)
        else:
            return JsonResponse(form.errors, status=400)

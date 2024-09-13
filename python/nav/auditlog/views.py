# coding: utf-8

# Copyright (C) 2017 Uninett AS
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


import json

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from nav.models.manage import Netbox
from nav.web.utils import create_title, get_navpath_root

from .models import LogEntry


class AuditlogOverview(TemplateView):
    model = LogEntry
    template_name = 'auditlog/overview.html'

    def get_context_data(self, **kwargs):
        verbs = list(
            LogEntry.objects.order_by().values_list('verb', flat=True).distinct()
        )
        verbs.sort()
        navpath = (get_navpath_root(), ('Audit Log',))
        context = {
            'auditlog_verbs': verbs,
            'navpath': navpath,
            'title': create_title(navpath),
        }
        context.update(**kwargs)
        return super(AuditlogOverview, self).get_context_data(**context)


class AuditlogNetboxDetail(AuditlogOverview):
    """Displays all log entries for a netbox"""

    def get_context_data(self, **kwargs):
        context = super(AuditlogNetboxDetail, self).get_context_data(**kwargs)
        context.update(
            {
                'auditlog_api_parameters': self.get_api_parameters(),
                'netbox': get_object_or_404(Netbox, pk=self.kwargs.get('netboxid')),
            }
        )
        return context

    def get_api_parameters(self):
        """Creates api parameters"""
        api_parameters = {}
        netboxid = self.kwargs.get('netboxid')
        if netboxid:
            api_parameters = {'netboxid': netboxid}
        return json.dumps(api_parameters)

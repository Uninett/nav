# coding: utf-8

# Copyright (C) 2017 UNINETT AS
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

from __future__ import unicode_literals, absolute_import

from django.views.generic import ListView, TemplateView

from .models import LogEntry


class AuditlogViewMixin(object):

    def get_context_data(self, **kwargs):
        tool = {
            'name': 'Auditlog',
            'description': 'Look up who/what did what with what',
        }
        context = {'tool': tool}
        context.update(**kwargs)
        return super(AuditlogViewMixin, self).get_context_data(**context)


class AuditlogOverview(AuditlogViewMixin, TemplateView):
    model = LogEntry
    template_name = 'auditlog/overview.html'

    def get_context_data(self, **kwargs):
        verbs = list(LogEntry.objects.order_by().values_list('verb', flat=True).distinct())
        verbs.sort()
        context = {
            'auditlog_verbs': verbs
        }
        context.update(**kwargs)
        return super(AuditlogOverview, self).get_context_data(**context)

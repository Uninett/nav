# coding: UTF-8

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
        qs = self.model.objects.values('actor_model', 'object_model',
                                       'target_model')
        actors, objects, targets = set(), set(), set()
        for row in qs:
            actors.add(row['actor_model'])
            objects.add(row['object_model'])
            targets.add(row['target_model'])
        objects.discard(None)
        targets.discard(None)
        context = {
            'actors': actors,
            'objects': objects,
            'targets': targets,
        }
        context.update(**kwargs)
        return super(AuditlogOverview, self).get_context_data(**context)


class AbstractAuditlogListView(AuditlogViewMixin, ListView):
    slug_url_kwarg = 'auditmodel'
    model = LogEntry
    template_name = 'auditlog/logentry_list.html'
    limit_to = None

    def get_context_data(self, **kwargs):
        context = {'auditmodel': self.kwargs.get(self.slug_url_kwarg, None)}
        context.update(**kwargs)
        return super(AbstractAuditlogListView, self).get_context_data(**context)

    def get_queryset(self):
        # Show only logs for specific object type
        qs = super(AbstractAuditlogListView, self).get_queryset()
        auditmodel = self.kwargs.get(self.slug_url_kwarg, None)
        if auditmodel and self.limit_to:
            kwargs = {self.limit_to: auditmodel}
            qs = qs.filter(**kwargs)
        return qs


class AuditlogObjectListView(AbstractAuditlogListView):
    limit_to = 'object_model'


class AuditlogActorListView(AbstractAuditlogListView):
    limit_to = 'actor_model'


class AuditlogTargetListView(AbstractAuditlogListView):
    limit_to = 'target_model'

# coding: UTF-8

from __future__ import unicode_literals

from django.views.generic import ListView, TemplateView
from django.contrib.contenttypes.models import ContentType

from auditlog.models import LogEntry
from auditlog import registry, find_modelname


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

    def get_context_data(self, **kwargs):
        context = {'auditmodel': self.kwargs.get(self.slug_url_kwarg, None)}
        context.update(**kwargs)
        return super(AbstractAuditlogListView, self).get_context_data(**context)


class AuditlogObjectListView(AbstractAuditlogListView):

    def get_queryset(self):
        # Show only logs for specific object type
        qs = super(AuditlogObjectListView, self).get_queryset()
        auditmodel = self.kwargs.get(self.slug_url_kwarg, None)
        if auditmodel:
            model = registry.get(auditmodel)
            qs = qs.filter(object_model=auditmodel)
        return qs


class AuditlogActorListView(AbstractAuditlogListView):

    def get_queryset(self):
        # Show only logs for specific actor type
        qs = super(AuditlogActorListView, self).get_queryset()
        auditmodel = self.kwargs.get(self.slug_url_kwarg, None)
        if auditmodel:
            model = registry.get(auditmodel)
            qs = qs.filter(actor_model=auditmodel)
        return qs


class AuditlogTargetListView(AbstractAuditlogListView):

    def get_queryset(self):
        # Show only logs for specific target type
        qs = super(AuditlogTargetListView, self).get_queryset()
        auditmodel = self.kwargs.get(self.slug_url_kwarg, None)
        if auditmodel:
            model = registry.get(auditmodel)
            qs = qs.filter(target_model=auditmodel)
        return qs

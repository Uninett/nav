from __future__ import unicode_literals

from django.conf.urls import *

from auditlog.views import *


urlpatterns = patterns('',
    url(r'^$', AuditlogOverview.as_view(), name='auditlog-home'),

    url(r'^object/*/$', AuditlogObjectListView.as_view(), name='auditlog-object-list-all'),
    url(r'^object/(?P<auditmodel>[-\w]+)/$', AuditlogObjectListView.as_view(), name='auditlog-object-list'),
    url(r'^actor/*/$', AuditlogActorListView.as_view(), name='auditlog-actor-list-all'),
    url(r'^actor/(?P<auditmodel>[-\w]+)/$', AuditlogActorListView.as_view(), name='auditlog-actor-list'),
    url(r'^target/*/$', AuditlogTargetListView.as_view(), name='auditlog-target-list-all'),
    url(r'^target/(?P<auditmodel>[-\w]+)/$', AuditlogTargetListView.as_view(), name='auditlog-target-list'),
)

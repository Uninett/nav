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

from django.conf.urls import url
from nav.auditlog import views


urlpatterns = [
    url(r'^$',
        views.AuditlogOverview.as_view(),
        name='auditlog-home'),
    url(r'^object/*/$',
        views.AuditlogObjectListView.as_view(),
        name='auditlog-object-list-all'),
    url(r'^object/(?P<auditmodel>[-\w]+)/$',
        views.AuditlogObjectListView.as_view(),
        name='auditlog-object-list'),
    url(r'^actor/*/$',
        views.AuditlogActorListView.as_view(),
        name='auditlog-actor-list-all'),
    url(r'^actor/(?P<auditmodel>[-\w]+)/$',
        views.AuditlogActorListView.as_view(),
        name='auditlog-actor-list'),
    url(r'^target/*/$',
        views.AuditlogTargetListView.as_view(),
        name='auditlog-target-list-all'),
    url(r'^target/(?P<auditmodel>[-\w]+)/$',
        views.AuditlogTargetListView.as_view(),
        name='auditlog-target-list'),
]

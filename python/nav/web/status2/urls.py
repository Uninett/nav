#
# Copyright (C) 2014 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from django.conf.urls import url, patterns, include
from nav.web.status2 import views

from rest_framework import routers

router = routers.SimpleRouter()
router.register('alert', views.AlertHistoryViewSet)

urlpatterns = patterns('',
    url(r'^$', views.StatusView.as_view(),
        name='status2-index'),
    url(r'^save_preferences/', views.save_status_preferences,
        name='status2_save_preferences'),
    url(r'^alert/resolve/', views.resolve_alerts,
        name='status2_clear_alert'),
    url(r'^alert/acknowledge/', views.acknowledge_alert,
        name='status2_acknowledge_alert'),
    url(r'^alert/put_on_maintenance/', views.put_on_maintenance,
        name='status2_put_on_maintenance'),
    url(r'^_api/', include(router.urls))
)

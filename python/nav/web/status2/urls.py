#
# Copyright (C) 2014 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL configuration for new status tool"""

from django.urls import re_path, path
from nav.web.status2 import views


urlpatterns = [
    path('', views.StatusView.as_view(), name='status2-index'),
    # XXX: This hits more than just "save_preferences/"...
    re_path(
        r'^save_preferences/',
        views.save_status_preferences,
        name='status2_save_preferences',
    ),
    re_path(
        r'^alert/resolve/', views.handle_resolve_alerts, name='status2_clear_alert'
    ),
    re_path(
        r'^alert/acknowledge/',
        views.acknowledge_alert,
        name='status2_acknowledge_alert',
    ),
    re_path(
        r'^alert/put_on_maintenance/',
        views.put_on_maintenance,
        name='status2_put_on_maintenance',
    ),
    re_path(
        r'^alert/delete_module_or_chassis/',
        views.delete_module_or_chassis,
        name='status2_delete_module_or_chassis',
    ),
]

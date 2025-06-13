#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""SeedDB Django URL config"""

from django.urls import re_path
from nav.web.maintenance import views


urlpatterns = [
    re_path(r'^$', views.redirect_to_calendar),
    re_path(r'^calendar/$', views.calendar, name='maintenance'),
    re_path(r'^calendar/$', views.calendar, name='maintenance-calendar'),
    re_path(
        r'^calendar/(?P<year>\d{4})/(?P<month>\d{1,2})$',
        views.calendar,
        name='maintenance-calendar',
    ),
    re_path(r'^active/$', views.active, name='maintenance-active'),
    re_path(r'^planned/$', views.planned, name='maintenance-planned'),
    re_path(r'^historic/$', views.historic, name='maintenance-historic'),
    re_path(r'^search/$', views.component_search, name='maintenance-component-search'),
    re_path(r'^new/$', views.edit, name='maintenance-new'),
    re_path(
        r'^new/(?P<start_time>\d{4}-\d{2}-\d{2})/$',
        views.edit,
        name='maintenance-new-date',
    ),
    re_path(r'^edit/(?P<task_id>\d+)/$', views.edit, name='maintenance-edit'),
    re_path(r'^view/(?P<task_id>\d+)/$', views.view, name='maintenance-view'),
    re_path(r'^cancel/(?P<task_id>\d+)/$', views.cancel, name='maintenance-cancel'),
    re_path(
        r'^addnetbox/$', views.add_box_to_maintenance, name='maintenance-add-netbox'
    ),
]

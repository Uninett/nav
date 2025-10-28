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

from django.urls import path
from django.urls import re_path

from nav.web.maintenance import views


urlpatterns = [
    path('', views.redirect_to_calendar),
    path('calendar/', views.calendar, name='maintenance-calendar'),
    re_path(
        r'^calendar/(?P<year>\d{4})/(?P<month>\d{1,2})$',
        views.calendar,
        name='maintenance-calendar',
    ),
    path('active/', views.active, name='maintenance-active'),
    path('planned/', views.planned, name='maintenance-planned'),
    path('historic/', views.historic, name='maintenance-historic'),
    path('search/', views.component_search, name='maintenance-component-search'),
    path(
        'selectcomponents/',
        views.component_select,
        name='maintenance-component-select',
    ),
    path('new/', views.edit, name='maintenance-new'),
    re_path(
        r'^new/(?P<start_time>\d{4}-\d{2}-\d{2})/$',
        views.edit,
        name='maintenance-new-date',
    ),
    path('edit/<int:task_id>/', views.edit, name='maintenance-edit'),
    path('view/<int:task_id>/', views.view, name='maintenance-view'),
    path('cancel/<int:task_id>/', views.cancel, name='maintenance-cancel'),
    path('addnetbox/', views.add_box_to_maintenance, name='maintenance-add-netbox'),
]

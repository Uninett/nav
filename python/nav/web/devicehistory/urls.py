#
# Copyright (C) 2008-2009 Uninett AS
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
"""Django URL configuration for devicehistory."""

from django.urls import path
from nav.web.devicehistory import views


urlpatterns = [
    path('', views.devicehistory_search, name='devicehistory-search'),
    path(
        'componentsearch/',
        views.devicehistory_component_search,
        name='devicehistory-component-search',
    ),
    path('history/', views.devicehistory_view, name='devicehistory-view'),
    path(
        'history/room/<path:room_id>/',
        views.devicehistory_view_room,
        name='devicehistory-view-room',
    ),
    path(
        'history/netbox/<int:netbox_id>/',
        views.devicehistory_view_netbox,
        name='devicehistory-view-netbox',
    ),
    path(
        'history/location/<str:location_id>/',
        views.devicehistory_view_location,
        name='devicehistory-view-location',
    ),
    path('registererror/', views.error_form, name='devicehistory-registererror'),
    path(
        'registererror/componentsearch/',
        views.registererror_component_search,
        name='devicehistory-registererror-component-search',
    ),
    path(
        'do_registererror/',
        views.register_error,
        name='devicehistory-do-registererror',
    ),
    path('delete_module/', views.delete_module, name='devicehistory-module'),
    path(
        'do_delete_module/',
        views.do_delete_module,
        name='devicehistory-do_delete_module',
    ),
]

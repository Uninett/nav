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

from django.urls import re_path
from nav.web.devicehistory import views


urlpatterns = [
    re_path(r'^$', views.devicehistory_search, name='devicehistory-search'),
    re_path(
        r'^componentsearch/$',
        views.devicehistory_component_search,
        name='devicehistory-component-search',
    ),
    re_path(r'^history/$', views.devicehistory_view, name='devicehistory-view'),
    re_path(
        r'^history/room/(?P<room_id>.+)/$',
        views.devicehistory_view_room,
        name='devicehistory-view-room',
    ),
    re_path(
        r'^history/netbox/(?P<netbox_id>\d+)/$',
        views.devicehistory_view_netbox,
        name='devicehistory-view-netbox',
    ),
    re_path(
        r'^history/location/(?P<location_id>.+)/$',
        views.devicehistory_view_location,
        name='devicehistory-view-location',
    ),
    re_path(r'^registererror/$', views.error_form, name='devicehistory-registererror'),
    re_path(
        r'^registererror/componentsearch/$',
        views.registererror_component_search,
        name='devicehistory-registererror-component-search',
    ),
    re_path(
        r'^do_registererror/$',
        views.register_error,
        name='devicehistory-do-registererror',
    ),
    re_path(r'^delete_module/$', views.delete_module, name='devicehistory-module'),
    re_path(
        r'^do_delete_module/$',
        views.do_delete_module,
        name='devicehistory-do_delete_module',
    ),
]

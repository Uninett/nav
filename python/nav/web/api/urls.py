#
# Copyright (C) 2013 UNINETT AS
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
#
# pylint: disable=E1101
"""Urlconf for the NAV REST api"""

from nav.web.api import views
from django.conf.urls import url, patterns

room_list = views.RoomViewSet.as_view({'get': 'list'})
room_detail = views.RoomViewSet.as_view({'get': 'retrieve'})
netbox_list = views.RoomViewSet.as_view({'get': 'list'})
netbox_detail = views.RoomViewSet.as_view({'get': 'retrieve'})
interface_list = views.InterfaceViewSet.as_view({'get': 'list'})
interface_detail = views.InterfaceViewSet.as_view({'get': 'retrieve'})
prefix_list = views.PrefixViewSet.as_view({'get': 'list'})
prefix_detail = views.PrefixViewSet.as_view({'get': 'retrieve'})

urlpatterns = patterns(
    "",
    url(r'^$', views.api_root, name="api-root"),
    url(r'^token/$', views.get_or_create_token, name="api-token"),

    url(r"^room/$", room_list, name="api-rooms"),
    url(r"^room/(?P<pk>\w+)$", room_detail, name="api-room"),

    url(r"^netbox/$", netbox_list, name="api-netboxes"),
    url(r"^netbox/(?P<pk>\d+)$", netbox_detail, name="api-netbox"),

    url(r"^interface/$", interface_list, name="api-interfaces"),
    url(r"^interface/(?P<pk>\d+)$", interface_detail, name="api-interface"),

    url(r"^prefix/$", prefix_list, name="api-prefixes"),
    url(r"^prefix/(?P<pk>\d+)$", prefix_detail, name="api-prefix"),

    url(r"^prefix/routed/?$", views.RoutedPrefixList.as_view(),
        name="api-prefixes-routed"),
    url(r"^activeip/(?P<prefix>.*)$", views.PrefixUsageDetail.as_view(),
        name="api-prefix-usage"),
)

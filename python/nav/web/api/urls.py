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

from django.conf.urls import url, patterns
from .views import (RoomList, RoomDetail, NetboxList, NetboxDetail,
                    PrefixUsageDetail, get_or_create_token, PrefixDetail,
                    PrefixList, RoutedPrefixList, api_root, InterfaceDetail,
                    InterfaceList)

urlpatterns = patterns(
    "",
    url(r"^$", api_root, name="api-inventory"),
    url(r"^token/$", get_or_create_token, name="api-token"),

    url(r"^room/$", RoomList.as_view(), name="api-rooms"),
    url(r"^room/(?P<pk>\w+)$", RoomDetail.as_view(), name="api-room"),

    url(r"^netbox/$", NetboxList.as_view(), name="api-netboxes"),
    url(r"^netbox/(?P<pk>\d+)$", NetboxDetail.as_view(), name="api-netbox"),

    url(r"^interface/$", InterfaceList.as_view(), name="api-interfaces"),
    url(r"^interface/(?P<pk>\d+)$", InterfaceDetail.as_view(),
        name="api-interface"),

    url(r"^prefix/routed/?$",
        RoutedPrefixList.as_view(), name="api-prefixes-routed"),
    url(r"^prefix/?$", PrefixList.as_view(), name="api-prefixes"),
    url(r"^prefix/(?P<pk>\d+)/?$", PrefixDetail.as_view(),
        name="api-prefix"),
    url(r"^activeip/(?P<prefix>.*)$", PrefixUsageDetail.as_view(),
        name="api-prefix-usage"),
)

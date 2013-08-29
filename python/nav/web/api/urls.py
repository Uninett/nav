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
                    PrefixUsageDetail, get_or_create_token)

urlpatterns = patterns(
    "",
    url(r"^$", RoomList.as_view(), name="api-inventory"),
    url(r"^token/$", get_or_create_token, name="api_token"),
    url(r"^rooms/$", RoomList.as_view(), name="api-rooms"),
    url(r"^rooms/(?P<pk>\w+)$", RoomDetail.as_view(), name="api-room"),
    url(r"^netboxes/$", NetboxList.as_view(), name="api-netboxes"),
    url(r"^netboxes/(?P<pk>\d+)$", NetboxDetail.as_view(), name="api-netbox"),
    url(r"^activeip/(?P<prefix>.*)$", PrefixUsageDetail.as_view(),
        name="api-prefix-usage"),
)

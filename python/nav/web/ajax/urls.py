#
# Copyright (C) 2012 Uninett AS
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
"""
Django URL configuration

The purpose of location /ajax/open is to put all ajax-requests that should be
available without logging in here so that we don't need more than one
web_access key for this.

The developer should make sure that the data exposed is indeed suitable
for open access.
"""

from django.urls import path
from nav.web.ajax import views


# URL's that does not require authorization
urlpatterns = [
    path(
        'open/roommapper/rooms/',
        views.get_rooms_with_position,
        name='room-positions',
    ),
    path(
        'open/roommapper/rooms/<str:roomid>/',
        views.get_rooms_with_position,
        name='room-position',
    ),
    path(
        'open/roommapper/locations/<str:locationid>/',
        views.get_rooms_with_position_for_location,
        name='location-position',
    ),
    path(
        'open/neighbormap/<int:netboxid>/',
        views.get_neighbors,
        name='ajax-get-neighbors',
    ),
]

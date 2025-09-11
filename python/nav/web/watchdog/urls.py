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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""URL config for WatchDog"""

from django.urls import path
from nav.web.watchdog import views


urlpatterns = [
    path('', views.render_index, name='watchdog-index'),
    path(
        'active_addresses',
        views.get_active_addresses,
        name='watchdog-active-addresses',
    ),
    path('serial_numbers', views.get_serial_numbers, name='watchdog-serial-numbers'),
    path('cam_and_arp', views.get_cam_and_arp, name='watchdog-cam-and-arp'),
    path('db_size', views.get_database_size, name='watchdog-db-size'),
]

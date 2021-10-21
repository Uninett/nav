#
# Copyright (C) 2009-2011, 2019 Uninett AS
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
"""URL configuration for Machinetracker tool"""

from django.urls import re_path
from nav.web.machinetracker import views


urlpatterns = [
    re_path(r'^$', views.ip_search, name='machinetracker'),
    re_path(r'^ip/$', views.ip_search, name='machinetracker-ip'),
    re_path(
        r'^ip/prefix/(?P<prefix_id>\d+)/$',
        views.ip_prefix_search,
        name='machinetracker-prefixid_search',
    ),
    re_path(
        r'^ip/prefix/(?P<prefix_id>\d+)/active/$',
        views.ip_prefix_search,
        {'active': True},
        name='machinetracker-prefixid_search_active',
    ),
    re_path(r'^mac/$', views.mac_search, name='machinetracker-mac'),
    re_path(r'^swp/$', views.switch_search, name='machinetracker-swp'),
    # NetBIOS
    re_path(r'^netbios/$', views.netbios_search, name='machinetracker-netbios'),
]

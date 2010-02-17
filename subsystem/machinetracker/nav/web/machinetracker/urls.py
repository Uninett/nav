# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""URL configuration for Machinetracker tool"""

from django.conf.urls.defaults import *

from nav.web.machinetracker.views import *

urlpatterns = patterns('',
    url(r'^$', ip,
        name='machinetracker-frontpage'),
    url(r'^ip/$', ip,
        name='machinetracker-ip'),
    url(r'^ip/search/$', ip_search,
        name='machinetracker-ip_search'),

    url(r'^mac/$', mac,
        name='machinetracker-mac'),
    url(r'^mac/search/$', 'mac_search',
        name='machinetracker-mac_search'),

    url(r'^swp/$', switch,
        name='machinetracker-swp'),
    url(r'swp/search/$', 'swp_search',
        name='machinetracker-swp_search'),
)

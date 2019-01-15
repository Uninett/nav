# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Uninett AS
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

from django.conf.urls import url
from nav.web.machinetracker import views


urlpatterns = [
    url(r'^$',
        views.ip_search,
        name='machinetracker'),
    url(r'^ip/$',
        views.ip_search,
        name='machinetracker-ip'),
    url(r'^ip/\?from_ip=(?P<from_ip>[^&]+)&to_ip=(?P<to_ip>[^&]*)'
        r'&active=(?P<active>\w*)&inactive=(?P<inactive>\w*)'
        r'&days=(?P<days>-?\d+)&dns=(?P<dns>\w*)$',
        views.ip_do_search,
        name='machinetracker-ip_search'),
    # Short hand search url.
    # Accepts from_ip, days and dns. Active is set to true
    url(r'^ip/\?ip_range=(?P<from_ip>[^&]+)&days=(?P<days>-?\d+)'
        r'&dns=(?P<dns>\w*)&period_filter=active',
        views.ip_do_search,
        name='machinetracker-ip_short_search'),

    url(r'^ip/\?prefixid=(?P<prefix_id>\d+)$',
        views.ip_do_search,
        name='machinetracker-prefixid_search'),
    url(r'^ip/\?prefixid=(?P<prefix_id>\d+)&days=-1$',
        views.ip_do_search,
        name='machinetracker-prefixid_search_active'),

    url(r'^mac/$',
        views.mac_search,
        name='machinetracker-mac'),
    url(r'^mac/\?mac=(?P<mac>[^&]+)'
        r'&days=(?P<days>-?\d+)&dns=(?P<dns>\w*)$',
        views.mac_do_search,
        name='machinetracker-mac_search'),

    url(r'^swp/$',
        views.switch_search,
        name='machinetracker-swp'),
    url(r'^swp/\?switch=(?P<switch>[^&]+)&module=(?P<module>\d*)'
        r'&port=(?P<port>[^&]*)$',
        views.switch_do_search,
        name='machinetracker-swp_short_search'),
    url(r'^swp/\?switch=(?P<switch>[^&]+)&module=(?P<module>\d*)'
        r'&port=(?P<port>[^&]*)&days=(?P<days>-?\d+)$',
        views.switch_do_search,
        name='machinetracker-swp_search'),

    # NetBIOS
    url(r'^netbios/$',
        views.netbios_search,
        name='machinetracker-netbios'),
    url(r'^netbios/\?search=(?P<search>[^&]+)&days=(?P<days>\d+)$',
        views.netbios_search,
        name='machinetracker-netbios-search'),

    # Old machinetrakcer links.
     url(r'^swp\?switch=(?P<netbox_sysname>[^&]+)'
         r'&module=(?P<module_number>\d+)'
         r'&port=(?P<port_interface>[^&]+)&days=7$',
         views.switch_do_search,
         name='machinetracker-swport'),
     url(r'^swp\?switch=(?P<netbox_sysname>[^&]+)'
         r'&port=(?P<port_interface>[^&]+)&days=7$',
         views.switch_do_search,
         name='machinetracker-swport'),
]

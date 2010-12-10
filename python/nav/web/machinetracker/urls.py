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

dummy = lambda *args, **kwargs: None

urlpatterns = patterns('',
    url(r'^$', ip_search,
        name='machinetracker'),
    url(r'^ip/$', ip_search,
        name='machinetracker-ip'),
    url(r'^ip/\?from_ip=(?P<from_ip>[a-f\d\.:]+)&to_ip=(?P<to_ip>[a-f-\d\.:]*)&active=(?P<active>\w*)&inactive=(?P<inactive>\w*)&days=(?P<days>-?\d+)&dns=(?P<dns>\w*)$',
        ip_do_search,
        name='machinetracker-ip_search'),
    # Short hand search url.
    # Accepts from_ip, days and dns. Active is set to true
    url(r'^ip/\?from_ip=(?P<from_ip>[a-f\d\.:]+)&days=(?P<days>-?\d+)&dns=(?P<dns>\w*)&active=on',
        ip_do_search,
        name='machinetracker-ip_short_search'),

    url(r'^ip/\?prefixid=(?P<prefix_id>\d+)$', ip_do_search,
        name='machinetracker-prefixid_search'),

    url(r'^mac/$', mac_search,
        name='machinetracker-mac'),
    url(r'^mac/\?mac=(?P<mac>[a-f\d:]+)&days=(?P<days>-?\d+)&dns=(?P<dns>\w*)$',
        mac_do_search,
        name='machinetracker-mac_search'),

    url(r'^swp/$', switch_search,
        name='machinetracker-swp'),
    url(r'^swp/\?switch=(?P<switch>[\w\d._-]+)&module=(?P<module>\d*)&port=(?P<port>[\w\.-/ \(\):]*)$',
        switch_do_search,
        name='machinetracker-swp_short_search'),
    url(r'^swp/\?switch=(?P<switch>[\w\d._-]+)&module=(?P<module>\d*)&port=(?P<port>[\w\.-/ \(\):]*)&days=(?P<days>-?\d+)$',
        switch_do_search,
        name='machinetracker-swp_search'),

     # Old machinetrakcer links.
     url(r'^swp\?switch=(?P<netbox_sysname>[\w\d._-]+)&module=(?P<module_number>\d+)&port=(?P<port_interface>[\w\.-/ \(\):]+)&days=7$',
         switch_do_search, name='machinetracker-swport'),
     url(r'^swp\?switch=(?P<netbox_sysname>[\w\d._-]+)&port=(?P<port_interface>[\w\.-/ \(\):]+)&days=7$',
         switch_do_search, name='machinetracker-swport'),
)

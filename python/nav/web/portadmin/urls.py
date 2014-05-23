#
# Copyright 2010 (C) Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""PortAdmin Django URL config"""

from django.conf.urls.defaults import patterns, url
from nav.web.portadmin.views import (index, search_by_ip, search_by_sysname,
                                     search_by_interfaceid,
                                     save_interfaceinfo, render_trunk_edit,
                                     restart_interface)

urlpatterns = patterns('',
    url(r'^$', index, name='portadmin-index'),

    url(r'^ip=(?P<ip>[\d\.]+)', search_by_ip,
        name='portadmin-ip'),
    url(r'^sysname=(?P<sysname>\S+)', search_by_sysname,
        name='portadmin-sysname'),
    url(r'^interfaceid=(?P<interfaceid>\d+)', search_by_interfaceid,
        name='portadmin-interface'),

    url(r'^save_interfaceinfo', save_interfaceinfo),
    url(r'^restart_interface', restart_interface),
    url(r'^trunk/(?P<interfaceid>\d+)', render_trunk_edit,
        name="portadmin-render-trunk-edit"),

)

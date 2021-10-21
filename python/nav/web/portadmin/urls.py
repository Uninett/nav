#
# Copyright (C) 2011, 2013-2015 Uninett AS
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
"""PortAdmin Django URL config"""

from django.urls import re_path
from nav.web.portadmin import views


urlpatterns = [
    re_path(r'^$', views.index, name='portadmin-index'),
    re_path(r'^ip=(?P<ip>[\d\.]+)', views.search_by_ip, name='portadmin-ip'),
    re_path(
        r'^sysname=(?P<sysname>\S+)', views.search_by_sysname, name='portadmin-sysname'
    ),
    re_path(
        r'^interfaceid=(?P<interfaceid>\d+)',
        views.search_by_interfaceid,
        name='portadmin-interface',
    ),
    re_path(r'^save_interfaceinfo', views.save_interfaceinfo),
    re_path(r'^restart_interfaces', views.restart_interfaces),
    re_path(r'^commit_configuration', views.commit_configuration),
    re_path(
        r'^trunk/(?P<interfaceid>\d+)',
        views.render_trunk_edit,
        name="portadmin-render-trunk-edit",
    ),
]

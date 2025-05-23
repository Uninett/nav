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
"""Django URL configuration"""

from django.urls import re_path
from nav.web.info.vlan import views


urlpatterns = [
    re_path(r'^$', views.index, name='vlan-index'),
    re_path(r'^(?P<vlanid>\d+)/$', views.vlan_details, name='vlan-details'),
    re_path(
        r'^graph/prefix/(?P<prefixid>\d+)$',
        views.create_prefix_graph,
        name='vlan-graph-prefix',
    ),
    re_path(
        r'^graph/vlan/(?P<vlanid>\d+)/(?P<family>\d)?$',
        views.create_vlan_graph,
        name='vlan-graph-prefix',
    ),
]

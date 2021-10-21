#
# Copyright (C) 2007-2008 Uninett AS
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
"""Django URL config for network explorer."""

from django.urls import re_path
from nav.web.networkexplorer import views


urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='networkexplorer-index'),
    re_path(r'^search/$', views.SearchView.as_view(), name="networkexplorer-search"),
    re_path(r'^routers/$', views.RouterJSONView.as_view(), name='networkexplorer-routers'),
    re_path(
        r'^expand/router/(?P<pk>\d+)/$',
        views.ExpandRouterView.as_view(),
        name='networkexplorer-expand-router',
    ),
    re_path(
        r'^expand/gwport/(?P<pk>\d+)/$',
        views.ExpandGWPortView.as_view(),
        name='networkexplorer-expand-gwport',
    ),
    re_path(
        r'^expand/switch/(?P<pk>\d+)/$',
        views.ExpandSwitchView.as_view(),
        name='networkexplorer-expand-switch',
    ),
    re_path(
        r'^expand/switch/(?P<pk>\d+)/vlan/(?P<vlan_id>\d+)/$',
        views.ExpandSwitchView.as_view(),
        name='networkexplorer-expand-switch-vlan',
    ),
    re_path(
        r'^expand/swport/(?P<pk>\d+)/$',
        views.ExpandSWPortView.as_view(),
        name='networkexplorer-expand-swport',
    ),
]

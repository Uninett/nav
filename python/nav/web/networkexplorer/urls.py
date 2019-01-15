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

from django.conf.urls import url
from nav.web.networkexplorer import views


urlpatterns = [
    url(r'^$',
        views.IndexView.as_view(),
        name='networkexplorer-index'),

    url(r'^search/$',
        views.SearchView.as_view(),
        name="networkexplorer-search"),

    url(r'^routers/$',
        views.RouterJSONView.as_view(),
        name='networkexplorer-routers'),

    url(r'^expand/router/(?P<pk>\d+)/$',
        views.ExpandRouterView.as_view(),
        name='networkexplorer-expand-router'),

    url(r'^expand/gwport/(?P<pk>\d+)/$',
        views.ExpandGWPortView.as_view(),
        name='networkexplorer-expand-gwport'),

    url(r'^expand/switch/(?P<pk>\d+)/$',
        views.ExpandSwitchView.as_view(),
        name='networkexplorer-expand-switch'),

    url(r'^expand/switch/(?P<pk>\d+)/vlan/(?P<vlan_id>\d+)/$',
        views.ExpandSwitchView.as_view(),
        name='networkexplorer-expand-switch-vlan'),

    url(r'^expand/swport/(?P<pk>\d+)/$',
        views.ExpandSWPortView.as_view(),
        name='networkexplorer-expand-swport'),
]

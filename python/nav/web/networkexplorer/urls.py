#
# Copyright (C) 2007-2008 Uninett AS
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
"""Django URL config for network explorer."""

from django.urls import path
from nav.web.networkexplorer import views


urlpatterns = [
    path('', views.IndexView.as_view(), name='networkexplorer-index'),
    path('search/', views.SearchView.as_view(), name="networkexplorer-search"),
    path('routers/', views.RouterJSONView.as_view(), name='networkexplorer-routers'),
    path(
        'expand/router/<int:pk>/',
        views.ExpandRouterView.as_view(),
        name='networkexplorer-expand-router',
    ),
    path(
        'expand/gwport/<int:pk>/',
        views.ExpandGWPortView.as_view(),
        name='networkexplorer-expand-gwport',
    ),
    path(
        'expand/switch/<int:pk>/',
        views.ExpandSwitchView.as_view(),
        name='networkexplorer-expand-switch',
    ),
    path(
        'expand/switch/<int:pk>/vlan/<int:vlan_id>/',
        views.ExpandSwitchView.as_view(),
        name='networkexplorer-expand-switch-vlan',
    ),
    path(
        'expand/swport/<int:pk>/',
        views.ExpandSWPortView.as_view(),
        name='networkexplorer-expand-swport',
    ),
]

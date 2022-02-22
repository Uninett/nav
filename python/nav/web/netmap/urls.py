#
# Copyright (C) 2012 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Netmap backend URL config."""

from django.urls import re_path
from django.views.decorators.cache import never_cache

from nav.web.netmap.api import (
    TrafficView,
    NetmapViewList,
    NetmapViewEdit,
    NetmapViewCreate,
    NetmapViewDefaultViewUpdate,
    NodePositionUpdate,
    NetmapGraph,
)

from nav.models.profiles import Account
from .views import (
    IndexView,
    NetmapAdminView,
)


urlpatterns = [
    re_path(r'^$', IndexView.as_view(), name='netmap-index'),
    re_path(r'^admin/$', NetmapAdminView.as_view(), name='netmap-admin'),
    re_path(r'^views/$', NetmapViewList.as_view(), name='netmap-view-list'),
    re_path(
        r'^views/(?P<viewid>[\d]+)/$',
        NetmapViewEdit.as_view(),
        name='netmap-view-edit',
    ),
    re_path(
        r'^views/create/$',
        NetmapViewCreate.as_view(),
        name='netmap-view-create',
    ),
    re_path(
        r'^views/default/$',
        NetmapViewDefaultViewUpdate.as_view(),
        {'owner': Account.DEFAULT_ACCOUNT},  # Find a more elegant solution?
        name='netmap-defaultview-global',
    ),
    re_path(
        r'^views/default/(?P<owner>[\d]+)/$',
        NetmapViewDefaultViewUpdate.as_view(),
        name='netmap-defaultview-user',
    ),
    re_path(
        r'^views/(?P<viewid>[\d]+)/nodepositions/update/$',
        NodePositionUpdate.as_view(),
        name='netmap-nodepositions-update',
    ),
    re_path(
        r'^graph/layer(?P<layer>[2|3])/$',
        NetmapGraph.as_view(),
        name='netmap-graph',
    ),
    re_path(
        r'^graph/layer(?P<layer>[2|3])/(?P<viewid>[\d]+)/$',
        NetmapGraph.as_view(),
        name='netmap-graph-view',
    ),
    re_path(
        r'^traffic/layer(?P<layer>[2|3])/(?P<roomid>.*)$',
        never_cache(TrafficView.as_view()),
        name='netmap-traffic-data-view',
    ),
]

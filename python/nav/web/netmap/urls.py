#
# Copyright (C) 2012 Uninett AS
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

from django.conf.urls import url
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
    url(r'^$', IndexView.as_view(), name='netmap-index'),
    url(r'^admin/$', NetmapAdminView.as_view(), name='netmap-admin'),
    url(r'^views/$', NetmapViewList.as_view(), name='netmap-view-list'),
    url(
        r'^views/(?P<viewid>[\d]+)/$',
        NetmapViewEdit.as_view(),
        name='netmap-view-edit',
    ),
    url(
        r'^views/create/$',
        NetmapViewCreate.as_view(),
        name='netmap-view-create',
    ),
    url(
        r'^views/default/$',
        NetmapViewDefaultViewUpdate.as_view(),
        {'owner': Account.DEFAULT_ACCOUNT},  # Find a more elegant solution?
        name='netmap-defaultview-global',
    ),
    url(
        r'^views/default/(?P<owner>[\d]+)/$',
        NetmapViewDefaultViewUpdate.as_view(),
        name='netmap-defaultview-user',
    ),
    url(
        r'^views/(?P<viewid>[\d]+)/nodepositions/update/$',
        NodePositionUpdate.as_view(),
        name='netmap-nodepositions-update',
    ),
    url(
        r'^graph/layer(?P<layer>[2|3])/$',
        NetmapGraph.as_view(),
        name='netmap-graph',
    ),
    url(
        r'^graph/layer(?P<layer>[2|3])/(?P<viewid>[\d]+)/$',
        NetmapGraph.as_view(),
        name='netmap-graph-view',
    ),
    url(
        r'^traffic/layer(?P<layer>[2|3])/(?P<roomid>.*)$',
        never_cache(TrafficView.as_view()),
        name='netmap-traffic-data-view',
    ),
]

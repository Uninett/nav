#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Radius backend URL config."""
from django.conf.urls import url
from nav.web.radius import views


urlpatterns = [
    url(r'^$', views.index,
        name='radius-index'),
    url(r'^logsearch$', views.log_search,
        name='radius-log_search'),
    url(r'^logdetail/(?P<accountid>\d+)/modal$', views.log_detail_modal,
        name='radius-log_detail-modal'),
    url(r'^logdetail/(?P<accountid>\d+)$', views.log_detail_page,
        name='radius-log_detail'),
    url(r'^acctdetail/(?P<accountid>\d+)/modal$', views.account_detail_modal,
        name='radius-account_detail-modal'),
    url(r'^acctdetail/(?P<accountid>\d+)$', views.account_detail_page,
        name='radius-account_detail'),
    url(r'^acctcharts$', views.account_charts,
        name='radius-account_charts'),
    url(r'^acctsearch$', views.account_search,
        name='radius-account_search')
]

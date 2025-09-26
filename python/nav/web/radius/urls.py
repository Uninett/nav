#
# Copyright (C) 2018 Uninett AS
# Copyright (C) 2022 Sikt
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

from django.urls import path
from nav.web.radius import views


urlpatterns = [
    path('', views.index, name='radius-index'),
    path('logsearch', views.log_search, name='radius-log_search'),
    path(
        'logsearch/searchhints',
        views.log_search_hints_modal,
        name='radius-error-log-hints',
    ),
    path(
        'logdetail/<int:accountid>/modal',
        views.log_detail_modal,
        name='radius-log_detail-modal',
    ),
    path(
        'logdetail/<int:accountid>',
        views.log_detail_page,
        name='radius-log_detail',
    ),
    path(
        'acctdetail/<int:accountid>/modal',
        views.account_detail_modal,
        name='radius-account_detail-modal',
    ),
    path(
        'acctdetail/<int:accountid>',
        views.account_detail_page,
        name='radius-account_detail',
    ),
    path('acctcharts', views.account_charts, name='radius-account_charts'),
    path(
        'acctcharts/acctcharthints',
        views.account_chart_hints_modal,
        name='radius-account-chart-hints',
    ),
    path('acctsearch', views.account_search, name='radius-account_search'),
    path(
        'acctsearch/acctloghints',
        views.account_log_hints_modal,
        name='radius-account-log-hints',
    ),
]

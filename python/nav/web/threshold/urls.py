#
# Copyright 2011 Uninett AS
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
"""url config for thresholds app"""

from django.urls import path, re_path
from nav.web.threshold import views


urlpatterns = [
    path('', views.index, name='threshold-index'),
    path('add', views.add_threshold, name='threshold-add'),
    re_path(r'^add/(?P<metric>.*)$', views.add_threshold, name='threshold-add'),
    path('edit/<int:rule_id>', views.edit_threshold, name='threshold-edit'),
    path('delete/<int:rule_id>', views.delete_threshold, name='threshold-delete'),
    path('helpmodal', views.threshold_help_modal, name='threshold-help-modal'),
    path('search/', views.threshold_search, name='threshold-search'),
    path('graph_url/', views.get_graph_url, name='threshold-graph'),
]

#
# Copyright 2011 Uninett AS
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

from django.urls import re_path
from nav.web.threshold import views


urlpatterns = [
    re_path(r'^$', views.index, name='threshold-index'),
    re_path(r'^add$', views.add_threshold, name='threshold-add'),
    re_path(r'^add/(?P<metric>.*)$', views.add_threshold, name='threshold-add'),
    re_path(r'^edit/(?P<rule_id>\d+)$', views.edit_threshold, name='threshold-edit'),
    re_path(r'^delete/(?P<rule_id>\d+)$', views.delete_threshold, name='threshold-delete'),
    re_path(r'^search/$', views.threshold_search, name='threshold-search'),
    re_path(r'^graph_url/$', views.get_graph_url, name='threshold-graph'),
]

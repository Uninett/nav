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

from django.conf.urls import url
from nav.web.threshold import views


urlpatterns = [
    url(r'^$',
        views.index,
        name='threshold-index'),
    url(r'^add$',
        views.add_threshold,
        name='threshold-add'),
    url(r'^add/(?P<metric>.*)$',
        views.add_threshold,
        name='threshold-add'),
    url(r'^edit/(?P<rule_id>\d+)$',
        views.edit_threshold,
        name='threshold-edit'),
    url(r'^delete/(?P<rule_id>\d+)$',
        views.delete_threshold,
        name='threshold-delete'),
    url(r'^search/$',
        views.threshold_search,
        name='threshold-search'),
    url(r'^graph_url/$',
        views.get_graph_url,
        name='threshold-graph'),
]

#
# Copyright 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""url config for thresholds app"""

from django.conf.urls import url, patterns
from nav.web.threshold.views import (index, threshold_search, get_graph_url,
                                     add_threshold, edit_threshold,
                                     delete_threshold)

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    url(r'^$', index, name='threshold-index'),
    url(r'^add$', add_threshold, name='threshold-add'),
    url(r'^add/(?P<metric>.*)$', add_threshold,
        name='threshold-add'),
    url(r'^edit/(?P<rule_id>\d+)$', edit_threshold,
        name='threshold-edit'),
    url(r'^delete/(?P<rule_id>\d+)$', delete_threshold,
        name='threshold-delete'),
    url(r'^search/$', threshold_search, name='threshold-search'),
    url(r'^graph_url/$', get_graph_url, name='threshold-graph'),
)

#
# Copyright (C) 2010 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Netmap backend URL config."""

from django.conf.urls.defaults import url, patterns

from nav.web.netmap.views import index, output_graph_data, category_list
from nav.web.netmap.views import linktype_list, save_positions

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    url(r'^$', index,
        name='netmap-index'),

    url(r'^server$', output_graph_data,
        name='netmap-graphdata'),
    url(r'^catids$', category_list,
        name='netmap-category-list'),
    url(r'^linktypes$', linktype_list,
        name='netmap-linktype-list'),
    url(r'^position$', save_positions,
        name='netmap-save-positions'),
)

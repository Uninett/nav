#
# Copyright (C) 2016 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""URL definitions for prefix details"""

from django.conf.urls import url
from nav.web.info.prefix import views


urlpatterns = [
    url(r'^$', views.index,
        name='prefix-index'),
    url(r'^(?P<prefix_id>\d+)/$', views.prefix_details,
        name='prefix-details'),
    url(r'^(?P<prefix_id>\d+)/addTags/$', views.prefix_add_tags,
        name='prefix-add-tags'),
    url(r'^(?P<prefix_id>\d+)/reloadTags/$', views.prefix_reload_tags,
        name='prefix-reload-tags'),
]

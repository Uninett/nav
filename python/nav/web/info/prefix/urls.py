#
# Copyright (C) 2016 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""URL definitions for prefix details"""

from django.urls import path
from nav.web.info.prefix import views


urlpatterns = [
    path('', views.index, name='prefix-index'),
    path('<int:prefix_id>/', views.prefix_details, name='prefix-details'),
    path('<int:prefix_id>/addTags/', views.prefix_add_tags, name='prefix-add-tags'),
    path(
        '<int:prefix_id>/reloadTags/',
        views.prefix_reload_tags,
        name='prefix-reload-tags',
    ),
]

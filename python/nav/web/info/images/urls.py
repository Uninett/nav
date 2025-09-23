#
# Copyright (C) 2017 Uninett AS
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
"""Django URL configuration"""

from django.urls import re_path
from nav.web.info.images import views


# XXX: error-prone re_paths!
urlpatterns = [
    re_path(r'^update_title', views.update_title, name='image-update-title'),
    re_path(r'^delete', views.delete_image, name='image-delete-image'),
    re_path(r'^update_priority', views.update_priority, name='image-update-priority'),
]

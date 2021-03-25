#
# Copyright (C) 2017 Uninett AS
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

from django.conf.urls import url
from nav.web.info.images import views


urlpatterns = [
    url(r'^update_title', views.update_title, name='image-update-title'),
    url(r'^delete', views.delete_image, name='image-delete-image'),
    url(r'^update_priority', views.update_priority, name='image-update-priority'),
]

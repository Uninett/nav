#
# Copyright (C) 2013 Uninett AS
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
"""Info netboxgroup url configuration"""

from django.urls import path
from django.urls import re_path
from nav.web.info.netboxgroup import views


urlpatterns = [
    path('', views.index, name='netbox-group'),
    re_path(r'^(?P<groupid>.+)/edit/', views.group_edit, name='netbox-group-edit'),
    re_path(r'^(?P<groupid>.+)', views.group_detail, name='netbox-group-detail'),
]

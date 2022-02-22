#
# Copyright (C) 2011 Uninett AS
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
"""macwatch Django URL config"""

from django.urls import re_path
from nav.web.macwatch import views


urlpatterns = [
    # Default view
    re_path(r'^$', views.list_watch, name='listwatch'),
    re_path(r'^add/$', views.add_macwatch),
    re_path(r'^delete/(\d+)/$', views.delete_macwatch),
    re_path(r'^edit/(\d+)/$', views.edit_macwatch),
]

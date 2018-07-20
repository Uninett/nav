# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 UNINETT AS
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
"""Django URL configuration for unrecognized neighbors system."""

from django.conf.urls import url
from nav.web.neighbors import views


urlpatterns = [
    url(r'^$', views.index,
        name='neighbors-index'),
    url(r'neighbor-state/', views.set_ignored_state,
        name='neighbors-set-state'),
]

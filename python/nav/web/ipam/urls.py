# -*- coding: utf-8 -*-
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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Django URL configuration.

Exposes a private, read-only API (self/api) for search purposes mostly.

"""

from django.urls import re_path, include
from nav.web.ipam.views import index, matrix
from nav.web.ipam.api import router


urlpatterns = [
    re_path(r'^$', index),
    re_path(r'^matrix', matrix),
    re_path(r'^api', include(router.urls)),
]

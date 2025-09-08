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

from django.urls import path, re_path, include

from nav.web.ipam.views import index, matrix, subnet_allocator_help_modal
from nav.web.ipam.api import router


urlpatterns = [
    path('', index),
    path('matrix', matrix),
    path('api', include(router.urls)),
    re_path(
        r'^subnetallocatorhelp',
        subnet_allocator_help_modal,
        name='ipam-subnet-allocator-help',
    ),
]

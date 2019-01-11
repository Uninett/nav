# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
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
"""syslogger Django URL config"""

from django.conf.urls import url
from nav.web.syslogger import views


urlpatterns = [
    url(r'^$', views.index,
        name='logger_index'),
    url(r'^search/group/$', views.group_search,
        name='logger_search_group'),
    url(r'^exceptions/$', views.exceptions_response,
        name='logger_priority_exceptions'),
    url(r'^errors/$', views.errors_response,
        name='logger_errors'),
]

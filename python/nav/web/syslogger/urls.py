# -*- coding: UTF-8 -*-
#
# Copyright (C) 2011 UNINETT AS
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
"""syslogger Django URL config"""

from django.conf.urls.defaults import patterns, url
from nav.web.syslogger.views import index
from nav.web.syslogger.views import exceptions_response
from nav.web.syslogger.views import errors_response
from nav.web.syslogger.views import group_search


urlpatterns = patterns('nav.web.syslogger.views',
    # Default view
    url(r'^$', index, name='logger_index'),
    url(r'^search/group/$', group_search, name='logger_search_group'),
    url(r'^exceptions/$', exceptions_response,
        name='logger_priority_exceptions'),
    url(r'^errors/$', errors_response, name='logger_errors'),
)

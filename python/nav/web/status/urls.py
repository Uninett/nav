# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""URL configuration for Status tool"""

from django.conf.urls.defaults import url, patterns

from nav.web.status.views import status, preferences, add_section
from nav.web.status.views import edit_preferences

urlpatterns = patterns('',
    url(r'^$', status,
        name='status-index'),
    url('^preferences/$', preferences,
        name='status-preferences'),
    url('^preferences/add-section/$', add_section,
        name='status-preferences-addsection'),
    url('^preferences/(?P<section_id>\d+)/$', edit_preferences,
        name='status-preferences-edit'),
)

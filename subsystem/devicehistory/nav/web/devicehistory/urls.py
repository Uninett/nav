# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL configuration for devicehistory."""

from django.conf.urls.defaults import *

from nav.web.devicehistory.views import *

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    # Search
    url(r'^$', devicehistory_search,
        name='devicehistory-search'),

    url(r'^history/$', devicehistory_view,
        name='devicehistory-view'),

    url(r'^registererror/$', error_form,
        name='devicehistory-registererror'),

    url(r'^delete_module/$', delete_module,
        name='devicehistory-module'),

    url(r'^do_delete_module/$', do_delete_module,
        name='devicehistory-do_delete_module'),
)


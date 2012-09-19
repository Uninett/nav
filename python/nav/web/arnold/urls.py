#
# Copyright (C) 2012 (SD -311000) UNINETT AS
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

from django.conf.urls.defaults import patterns, include, url
from nav.web.arnold.views import index, history, detainedports

urlpatterns = patterns('',
   url(r'^$', index, name="arnold_index"),
   url(r'^history/$', history, name="arnold-history"),
   url(r'^detainedports/$', detainedports, name="arnold-detainedports"),
)


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
"""macwatch Django URL config"""

from django.conf.urls.defaults import patterns, url
from nav.web.macwatch.views import list_watch, add_macwatch, delete_macwatch
from nav.web.macwatch.views import edit_macwatch

urlpatterns = patterns('',
    # Default view
    url(r'^$', list_watch, name='listwatch'),
    url(r'^add/$', add_macwatch),
    url(r'^delete/(\d+)/$', delete_macwatch),
    url(r'^edit/(\d+)/$', edit_macwatch),
)

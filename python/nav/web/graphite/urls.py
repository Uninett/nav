#
# Copyright (C) 2013 Uninett AS
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
"""Django URL config for graphite bridging"""

from django.conf.urls import url
from nav.web.graphite import views

_dummy = lambda x: None

urlpatterns = [
    url(r'^(?P<uri>.*)$', views.index, name='graphite'),
    url(r'^render', _dummy, name='graphite-render'),
    url(r'^metrics/find\?query=(?P<path>)$', _dummy, name='graphite-find'),
]

#
# Copyright (C) 2007-2008 UNINETT AS
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
"""Django URL config for network explorer."""

# pylint: disable-msg=W0614,W0401

from django.conf.urls.defaults import url, patterns

from nav.web.networkexplorer.views import *

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    url(r'^$', index,
        name='networkexplorer-index'),
    url(r'^expand/router', expand_router,
        name="networkexplorer-expand-router"),
    url(r'^expand/gwport', expand_gwport,
        name="networkexplorer-expand-gwport"),
    url(r'^expand/swport', expand_swport,
        name="networkexplorer-expand-swport"),
    url(r'^expand/switch', expand_switch,
        name="networkexplorer-expand-switch"),
    url(r'^search', search ,
        name="networkexplorer-search"),
)


# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Kristian Klette <kristian.klette@uninett.no>
#

__copyright__ = "Copyright 2007-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Kristian Klette (kristian.klette@uninett.no)"
__id__ = "$Id$"

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


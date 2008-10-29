# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

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
)


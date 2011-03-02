# -*- coding: utf-8 -*-
#
# Copyright 2010 UNINETT AS
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
# Authors: Fredrik Skolmli <fredrik.skolmli@uninett.no>
#

__copyright__ = "Copyright 2010 UNINETT AS"
__license__ = "GPL"
__author__ = "Fredrik Skolmli (fredrik.skolmli@uninett.no)"
__id__ = "$Id$"

from django.conf.urls.defaults import *
from nav.web.threshold.views import threshold_list, threshold_edit

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    # List accounts and groups
    url(r'^$', threshold_list, name='threshold-list'),
    url(r'^(?P<all>\w{3})/$', threshold_list, name='threshold-all'),
    url(r'^edit/(?P<threshold_id>\d+)/$', threshold_edit, name='threshold-edit'),
)

# -*- coding: utf-8 -*-
#
# Copyright 2011 UNINETT AS
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
#

__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal <john.m.bredal@ntnu.no> and Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"

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

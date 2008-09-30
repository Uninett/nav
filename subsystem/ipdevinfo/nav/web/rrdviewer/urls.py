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
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

from django.conf.urls.defaults import *

from nav.web.rrdviewer.views import *

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    url(r'^$', rrd_index,
        name='rrdviewer-index'),
    url(r'^ds=(?P<rrddatasource_id>\d+)/$', rrd_details,
        name='rrdviewer-rrd-by-ds'),
    url(r'^ds=(?P<rrddatasource_id>\d+)/tf=(?P<time_frame>\w+)/$', rrd_details,
        name='rrdviewer-rrd-by-ds-tf'),
    url(r'^image=(?P<rrdfile_id>\d+)/$', rrd_image,
        name='rrdviewer-rrd-image'),
)

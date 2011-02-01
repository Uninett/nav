# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 UNINETT AS
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
"""Django URL config for rrd viewer"""

from django.conf.urls.defaults import url, patterns

from nav.web.rrdviewer.views import rrd_index, rrd_details, rrd_image

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

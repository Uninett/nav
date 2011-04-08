#
# Copyright (C) 2009, 2010 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL config for geomap"""

from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('nav.web.geomap.views',
    url(r'^$', 'forward_to_default_variant', name='geomap-forward'),
    url(r'^([^/]+)/$', 'geomap', name='geomap'),
    url(r'^([^/]+)/data$', 'data', name='geomap-data'),
)

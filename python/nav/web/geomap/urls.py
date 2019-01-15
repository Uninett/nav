#
# Copyright (C) 2009, 2010 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL config for geomap"""

from django.conf.urls import url
from nav.web.geomap import views


urlpatterns = [
    url(r'^$', views.forward_to_default_variant, name='geomap-forward'),
    url(r'^([^/]+)/$', views.geomap, name='geomap'),
    url(r'^([^/]+)/data$', views.data, name='geomap-data'),
]

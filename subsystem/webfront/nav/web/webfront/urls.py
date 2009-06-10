# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Django URL configuration for webfront"""

from django.conf.urls.defaults import *

from nav.web.webfront.views import *

urlpatterns = patterns('',
    url(r'^$', 'index',
        name='webfront-index'),
    url(r'^index/', 'index',
        name='webfront-index-index'),
    url(r'^login/', 'login'
        name='webfront-login'),
    url(r'^about/', 'about',
        name='webfront-about'),
    url(r'^toolbox/', 'toolbox',
        name='webfront-toolbox'),
)

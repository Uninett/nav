#
# Copyright 2010 (C) Norwegian University of Science and Technology
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
from django.conf.urls.defaults import *
from nav.web.portadmin.views import *

urlpatterns = patterns('',
    url(r'^$', index),
    url(r'^ip=(?P<ip>[\d\.]+)', search_by_ip),
    url(r'^sysname=(?P<sysname>\S+)', search_by_sysname),
    url(r'^interfaceid=(?P<interfaceid>\d+)', search_by_interfaceid),
    url(r'^save_interfaceinfo', save_interfaceinfo),
   )

# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 UNINETT AS
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

from nav.web.ipdevinfo.views import *

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    # Search
    url(r'^$', search,
        name='ipdevinfo-search'),

    # Service list
    url(r'^service/$', service_list,
        name='ipdevinfo-service-list-all'),
    url(r'^service/handler=(?P<handler>\w+)/$', service_list,
        name='ipdevinfo-service-list-handler'),

    # Service matrix
    url(r'^service/matrix/$', service_matrix,
        name='ipdevinfo-service-matrix'),

    # IP Device details
    url(r'^(?P<name>[\w\d\.-]+)/$', ipdev_details,
        name='ipdevinfo-details-by-name'),
    url(r'^ip=(?P<addr>[a-f\d\.:]+)/$', ipdev_details,
        name='ipdevinfo-details-by-addr'),
    url(r'^id=(?P<netbox_id>\d+)/$', ipdev_details,
        name='ipdevinfo-details-by-id'),

    # Module details
    url(r'^(?P<netbox_sysname>[\w\d\.-]+)/module=(?P<module_name>.+)/$',
        module_details, name='ipdevinfo-module-details'),

    # Interface details
    url(r'^(?P<netbox_sysname>[\w\d\.-]+)/interface=(?P<port_id>\d+)/$',
        port_details, name='ipdevinfo-interface-details'),
    url(r'^(?P<netbox_sysname>[\w\d\.-]+)/interface=(?P<port_name>[\w\d\.-/_]+)/$',
        port_details, name='ipdevinfo-interface-details'),
)


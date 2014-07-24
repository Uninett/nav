# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 UNINETT AS
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
"""Django URL config for ipdevinfo"""

from django.conf.urls.defaults import url, patterns

from nav.web.ipdevinfo.views import (search, service_list, service_matrix,
                                     port_counter_graph)
from nav.web.ipdevinfo.views import (ipdev_details, module_details,
                                     port_details, get_port_view, render_affected,
                                     get_graphite_render_url, render_host_info)

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
    url(r'^ip=(?P<addr>[a-f\d\.:]+)/$', ipdev_details,
        name='ipdevinfo-details-by-addr'),
    url(r'^id=(?P<netbox_id>\d+)/$', ipdev_details,
        name='ipdevinfo-details-by-id'),
    url(r'^(?P<name>[^/]+)/$', ipdev_details,
        name='ipdevinfo-details-by-name'),

    # Module details
    url(r'^(?P<netbox_sysname>[^/]+)/module=(?P<module_name>.+)/$',
        module_details, name='ipdevinfo-module-details'),

    # Interface details
    url(r'^(?P<netbox_sysname>[^/]+)/interface=(?P<port_id>\d+)/$',
        port_details, name='ipdevinfo-interface-details'),
    url(r'^(?P<netbox_sysname>[^/]+)/ifname=(?P<port_name>[^&]+)/$',
        port_details, name='ipdevinfo-interface-details-by-name'),
    url(r'^g/port/(?P<interfaceid>\d+)/$', port_counter_graph,
        name='interface-counter-graph'),
    url(r'^g/port/(?P<interfaceid>\d+)/(?P<kind>[^/]+)/$', port_counter_graph,
        name='interface-counter-graph'),

    # Modules
    url(r'^(?P<netbox_sysname>.+)/modules/(?P<perspective>\w+)/$',
        get_port_view, name='ipdevinfo-get-port-view'),

    # What happens if the device goes down
    url(r'(?P<netboxid>\d+)/affected', render_affected,
        name="ipdevinfo-affected"),

    # DNS
    url(r'hostinfo/(?P<identifier>.+)', render_host_info,
        name="ipdevinfo-hostinfo"),

    #metrics
    url(r'graphite-render/(?P<metric>.+)/$', get_graphite_render_url,
        name="graphite-render-url")

)

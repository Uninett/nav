# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL config for ipdevinfo"""

from django.urls import re_path
from nav.web.ipdevinfo import views


urlpatterns = [
    # Search
    re_path(r'^$', views.search, name='ipdevinfo-search'),
    # Service list
    re_path(r'^service/$', views.service_list, name='ipdevinfo-service-list-all'),
    re_path(
        r'^service/handler=(?P<handler>\w+)/$',
        views.service_list,
        name='ipdevinfo-service-list-handler',
    ),
    # Service matrix
    re_path(
        r'^service/matrix/$', views.service_matrix, name='ipdevinfo-service-matrix'
    ),
    # IP Device details
    re_path(
        r'^ip=(?P<addr>[a-f\d\.:]+)/$',
        views.ipdev_details,
        name='ipdevinfo-details-by-addr',
    ),
    re_path(
        r'^id=(?P<netbox_id>\d+)/$', views.ipdev_details, name='ipdevinfo-details-by-id'
    ),
    re_path(
        r'^(?P<name>[^/]+)/$', views.ipdev_details, name='ipdevinfo-details-by-name'
    ),
    re_path(
        r'^save_port_layout_pref',
        views.save_port_layout_pref,
        name='ipdevinfo-save-port-layout',
    ),
    # Module details
    re_path(
        r'^(?P<netbox_sysname>[^/]+)/module=(?P<module_name>.+)/$',
        views.module_details,
        name='ipdevinfo-module-details',
    ),
    # PoE details
    re_path(
        r'^(?P<netbox_sysname>[^/]+)/poegroup=(?P<grpindex>.+)/$',
        views.poegroup_details,
        name='ipdevinfo-poegroup-details',
    ),
    # Interface details
    re_path(
        r'^(?P<netbox_sysname>[^/]+)/interface=(?P<port_id>\d+)/$',
        views.port_details,
        name='ipdevinfo-interface-details',
    ),
    re_path(
        r'^(?P<netbox_sysname>[^/]+)/ifname=(?P<port_name>[^&]+)/$',
        views.port_details,
        name='ipdevinfo-interface-details-by-name',
    ),
    re_path(
        r'^g/port/(?P<interfaceid>\d+)/$',
        views.port_counter_graph,
        name='interface-counter-graph',
    ),
    re_path(
        r'^g/port/(?P<interfaceid>\d+)/(?P<kind>[^/]+)/$',
        views.port_counter_graph,
        name='interface-counter-graph',
    ),
    # Modules
    re_path(
        r'^(?P<netbox_sysname>.+)/modules/(?P<perspective>\w+)/$',
        views.get_port_view,
        name='ipdevinfo-get-port-view',
    ),
    # What happens if the device goes down
    re_path(
        r'(?P<netboxid>\d+)/affected', views.render_affected, name="ipdevinfo-affected"
    ),
    # DNS
    re_path(
        r'hostinfo/(?P<identifier>.+)',
        views.render_host_info,
        name="ipdevinfo-hostinfo",
    ),
    # Sensors
    re_path(r'sensor/(?P<identifier>.+)', views.sensor_details, name="sensor-details"),
    re_path(
        r'^(?P<netboxid>\d+)/unrecognized_neighbors',
        views.unrecognized_neighbors,
        name='ipdevinfo-unrecognized_neighbors',
    ),
]

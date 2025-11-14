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

from django.urls import path, re_path
from nav.web.ipdevinfo import views


urlpatterns = [
    # Search
    path('', views.search, name='ipdevinfo-search'),
    # Service list
    path('service/', views.service_list, name='ipdevinfo-service-list-all'),
    path(
        'service/handler=<str:handler>/',
        views.service_list,
        name='ipdevinfo-service-list-handler',
    ),
    # Service matrix
    path('service/matrix/', views.service_matrix, name='ipdevinfo-service-matrix'),
    # IP Device details
    re_path(
        r'^ip=(?P<addr>[a-f\d\.:]+)/$',
        views.ipdev_details,
        name='ipdevinfo-details-by-addr',
    ),
    path('id=<int:netbox_id>/', views.ipdev_details, name='ipdevinfo-details-by-id'),
    path('<str:name>/', views.ipdev_details, name='ipdevinfo-details-by-name'),
    re_path(
        r'^save_port_layout_pref',
        views.save_port_layout_pref,
        name='ipdevinfo-save-port-layout',
    ),
    # Module details
    path(
        '<str:netbox_sysname>/module=<path:module_name>/',
        views.module_details,
        name='ipdevinfo-module-details',
    ),
    # PoE details
    path(
        '<str:netbox_sysname>/poegroup=<str:grpindex>/',
        views.poegroup_details,
        name='ipdevinfo-poegroup-details',
    ),
    re_path(
        r'^poe-status-info-modal',
        views.poe_status_hint_modal,
        name='ipdevinfo-poe-status-hint-modal',
    ),
    re_path(
        r'^poe-classification-info-modal',
        views.poe_classification_hint_modal,
        name='ipdevinfo-poe-classification-hint-modal',
    ),
    # Interface details
    path(
        '<str:netbox_sysname>/interface=<int:port_id>/',
        views.port_details,
        name='ipdevinfo-interface-details',
    ),
    re_path(
        r'^(?P<netbox_sysname>[^/]+)/ifname=(?P<port_name>[^&]+)/$',
        views.port_details,
        name='ipdevinfo-interface-details-by-name',
    ),
    path(
        'g/port/<int:interfaceid>/',
        views.port_counter_graph,
        name='interface-counter-graph',
    ),
    path(
        'g/port/<int:interfaceid>/<kind>/',
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
    re_path(
        r'^(?P<netbox_sysname>[^/]+)/(?P<job_name>[^/]+)/refresh_job',
        views.refresh_ipdevinfo_job,
        name='refresh-ipdevinfo-job',
    ),
    re_path(
        r'^(?P<netbox_sysname>[^/]+)/(?P<job_name>[^/]+)/(?P<job_started_timestamp>[^/]+)/refresh_job_status',
        views.refresh_ipdevinfo_job_status_query,
        name='refresh-ipdevinfo-job-status-query',
    ),
]

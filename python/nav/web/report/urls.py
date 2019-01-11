#
# Copyright (C) 2012-2018 Uninett AS
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
"""Report backend URL config."""


from django.conf.urls import url
from nav.web.report import views


# Subsystem: Report
# Naming convention: report-<result>-<query>
urlpatterns = [
    url(r'^$', views.index,
        name='report-index'),
    url(r'^matrix$', views.matrix_report,
        name='report-matrix'),
    url(r'^matrix\?scope=(?P<scope>[^&]+)$', views.matrix_report,
        name='report-matrix-scope'),
    url(r'^matrix\?scope=(?P<scope>[^&]+)'
        r'&show_unused_addresses=(?P<show_unused_addresses>True|False)',
        views.matrix_report,
        name='report-matrix-scope-show_unused'),
    url(r'^reportlist$', views.report_list,
        name='report-reportlist'),
    url(r'^(?P<report_name>[^/]+)$', views.get_report,
        name='report-by-name'),
    url(r'^widget/add/', views.add_report_widget,
        name='report-add-widget'),
    url(r'^widget/(?P<report_name>[^/]+)$', views.get_report_for_widget,
        name='widget-report-by-name'),
]

dummy = lambda *args, **kwargs: None

# Reverse urls for known reports shipped by NAV
# .* wildcard match for unknown reports but is hopefully defined
# in report.conf
urlpatterns += [
    # Subsystem: Report
    # Naming convention: report-<result>-<query>

    url(r'^org$',
        dummy, name='report-organization-all'),
    url(r'^org\?orgid=(?P<organization_id>[^&]+)$',
        dummy, name='report-organization-organization'),

    url(r'^type$',
        dummy, name='report-type-all'),
    url(r'^type\?typeid=(?P<type_id>\d+)$',
        dummy, name='report-type-type'),

    url(r'^room$',
        dummy, name='report-room-all'),
    url(r'^room\?locationid=(?P<location_id>[^&]+)$',
        dummy, name='report-room-location'),

    url(r'^netbox$',
        dummy, name='report-netbox-all'),
    url(r'^netbox\?roomid=(?P<room_id>[^&]+)$',
        dummy, name='report-netbox-room'),
    url(r'^netbox\?catid=(?P<category_id>[\w\d._-]+)$',
        dummy, name='report-netbox-category'),

    url(r'^modules$',
        dummy, name='report-modules-all'),
    url(r'^modules\?netboxid=(?P<netbox_id>\d+)$',
        dummy, name='report-modules-netbox'),
    url(r'^modules\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_number>\d+)$',
        dummy, name='report-modules-module'),

    url(r'^interfaces\?netboxid=(?P<netbox_id>\d+)$',
        dummy, name='report-interfaces-netbox'),

    url(r'^gwport$',
        dummy, name='report-gwport-all'),
    url(r'^gwport\?netboxid=(?P<netbox_id>\d+)$',
        dummy, name='report-gwport-netbox'),
    url(r'^gwport\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_name>[^&]+)$',
        dummy, name='report-gwport-module'),

    url(r'^swport$',
        dummy, name='report-swport-all'),
    url(r'^swport\?netboxid=(?P<netbox_id>\d+)$',
        dummy, name='report-swport-netbox'),
    url(r'^swport\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_name>[^&]+)$',
        dummy, name='report-swport-module'),

    url(r'^swporttrunk$',
        dummy, name='report-swporttrunk-all'),
    url(r'^swporttrunk\?vlan=(?P<vlan>\d+)$',
        dummy, name='report-swporttrunk-vlan'),
    url(r'^swporttrunk\?vlanid=(?P<vlanid>\d+)$',
        dummy, name='report-swporttrunk-vlanid'),

    url(r'^prefix$',
        dummy, name='report-prefix-all'),
    url(r'^prefix\?prefixid=(?P<prefix_id>\d+)$',
        dummy, name='report-prefix-prefix'),
    url(r'^prefix\?netaddr=(?P<netaddr>[^&]+)&op_netaddr=like$',
        dummy, name='report-prefix-netaddr'),

    url(r'^topology_candidates$',
        dummy, name='report-topology-candidates-all'),
    url(r'^topology_candidates\?from_device=(?P<sysname>[^/&]+)$',
        dummy, name='report-topology-candidates-netbox'),
    url(r'^topology_candidates\?from_device=(?P<sysname>[^/&]+)&'
        r'from_interface=(?P<ifname>[^&]+)$',
        dummy, name='report-topology-candidates-port'),

]

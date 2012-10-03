#
# Copyright (C) 2012 UNINETT AS
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
"""Report backend URL config."""

from django.conf.urls.defaults import url, patterns
from nav.web.report import organization_all, organization_id, type_all, type_id, \
room_all, room_location, netbox_all, netbox_room, netbox_category, modules_all, \
modules_netbox, modules_module, interfaces_netbox, gwport_all, gwport_netbox, \
gwport_module, swport_all, swport_netbox, swport_module, swporttrunk_all, \
swporttrunk_vlan, swporttrunk_vlanid, prefix_all, prefix_prefix

# Subsystem: Report
# Naming convention: report-<result>-<query>
urlpatterns = patterns('nav.web.report.views',
    url(r'^report/org$',
        organization_all, name='report-organization-all'),
    url(r'^report/org\?orgid=(?P<organization_id>[^&]+)$',
        organization_id, name='report-organization-organization'),

    url(r'^report/type$',
        type_all, name='report-type-all'),
    url(r'^report/type\?typeid=(?P<type_id>\d+)$',
        type_id, name='report-type-type'),

    url(r'^report/room$',
        room_all, name='report-room-all'),
    url(r'^report/room\?locationid=(?P<location_id>[^&]+)$',
        room_location, name='report-room-location'),

    url(r'^report/netbox$',
        netbox_all, name='report-netbox-all'),
    url(r'^report/netbox\?roomid=(?P<room_id>[^&]+)$',
        netbox_room, name='report-netbox-room'),
    url(r'^report/netbox\?catid=(?P<category_id>[\w\d._-]+)$',
        netbox_category, name='report-netbox-category'),

    url(r'^report/modules$',
        modules_all, name='report-modules-all'),
    url(r'^report/modules\?netboxid=(?P<netbox_id>\d+)$',
        modules_netbox, name='report-modules-netbox'),
    url(r'^report/modules\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_number>\d+)$',
        modules_module, name='report-modules-module'),

    url(r'^report/interfaces\?netboxid=(?P<netbox_id>\d+)$',
        interfaces_netbox, name='report-interfaces-netbox'),

    url(r'^report/gwport$',
        gwport_all, name='report-gwport-all'),
    url(r'^report/gwport\?netboxid=(?P<netbox_id>\d+)$',
        gwport_netbox, name='report-gwport-netbox'),
    url(r'^report/gwport\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_name>[^&]+)$',
        gwport_module, name='report-gwport-module'),

    url(r'^report/swport$',
        swport_all, name='report-swport-all'),
    url(r'^report/swport\?netboxid=(?P<netbox_id>\d+)$',
        swport_netbox, name='report-swport-netbox'),
    url(r'^report/swport\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_name>[^&]+)$',
        swport_module, name='report-swport-module'),

    url(r'^report/swporttrunk$',
        swporttrunk_all, name='report-swporttrunk-all'),
    url(r'^report/swporttrunk\?vlan=(?P<vlan>\d+)$',
        swporttrunk_vlan, name='report-swporttrunk-vlan'),
    url(r'^report/swporttrunk\?vlanid=(?P<vlanid>\d+)$',
        swporttrunk_vlanid, name='report-swporttrunk-vlanid'),

    url(r'^report/prefix$',
        prefix_all, name='report-prefix-all'),
    url(r'^report/prefix\?prefixid=(?P<prefix_id>\d+)$',
        prefix_prefix, name='report-prefix-prefix'),
)
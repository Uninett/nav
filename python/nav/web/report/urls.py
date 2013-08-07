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
from nav.web.report.views import get_report, matrix_report, index, report_list

# Subsystem: Report
# Naming convention: report-<result>-<query>
urlpatterns = patterns('nav.web.report.views',
    url(r'^$', index, name='report-index'),
    url(r'^matrix$',
        matrix_report, name='report-matrix'),
    url(r'^matrix\?scope=(?P<scope>[^&]+)$',
        matrix_report, name='report-matrix-scope'),
    url(r'^matrix\?scope=(?P<scope>[^&]+)'
        r'&show_unused_addresses=(?P<show_unused_addresses>True|False)',
        matrix_report, name='report-matrix-scope-show_unused'),
    url(r'^reportlist$',
        report_list, name='report-reportlist'),
    url(r'^(?P<report_name>[^/]+)$',
        get_report, name='report-by-name')
)

dummy = lambda *args, **kwargs: None

# Reverse urls for known reports shipped by NAV
# .* wildcard match for unknown reports but is hopefully defined
# in report.conf
urlpatterns += patterns('nav.web.report.views',
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
)

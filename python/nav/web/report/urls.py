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
from nav.web.report.reports import get_report, matrix_report, index, report_list

# Subsystem: Report
# Naming convention: report-<result>-<query>
urlpatterns = patterns('nav.web.report.views',
    url(r'^$', index, name='report-index'),
    url(r'^matrix',
        matrix_report, name='report-matrix'),
    url(r'^reportlist$',
        report_list, name='report-reportlist'),
)

# Reverse urls for known reports shipped by NAV
# .* wildcard match for unknown reports but is hopefully defined
# in report.conf
urlpatterns += patterns('nav.web.report.views',
    # Subsystem: Report
    # Naming convention: report-<result>-<query>

    url(r'^org$',
        get_report, name='report-organization-all'),
    url(r'^org\?orgid=(?P<organization_id>[^&]+)$',
        get_report, name='report-organization-organization'),

    url(r'^type$',
        get_report, name='report-type-all'),
    url(r'^type\?typeid=(?P<type_id>\d+)$',
        get_report, name='report-type-type'),

    url(r'^room$',
        get_report, name='report-room-all'),
    url(r'^room\?locationid=(?P<location_id>[^&]+)$',
        get_report, name='report-room-location'),

    url(r'^netbox$',
        get_report, name='report-netbox-all'),
    url(r'^netbox\?roomid=(?P<room_id>[^&]+)$',
        get_report, name='report-netbox-room'),
    url(r'^netbox\?catid=(?P<category_id>[\w\d._-]+)$',
        get_report, name='report-netbox-category'),

    url(r'^modules$',
        get_report, name='report-modules-all'),
    url(r'^modules\?netboxid=(?P<netbox_id>\d+)$',
        get_report, name='report-modules-netbox'),
    url(r'^modules\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_number>\d+)$',
        get_report, name='report-modules-module'),

    url(r'^interfaces\?netboxid=(?P<netbox_id>\d+)$',
        get_report, name='report-interfaces-netbox'),

    url(r'^gwport$',
        get_report, name='report-gwport-all'),
    url(r'^gwport\?netboxid=(?P<netbox_id>\d+)$',
        get_report, name='report-gwport-netbox'),
    url(r'^gwport\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_name>[^&]+)$',
        get_report, name='report-gwport-module'),

    url(r'^swport$',
        get_report, name='report-swport-all'),
    url(r'^swport\?netboxid=(?P<netbox_id>\d+)$',
        get_report, name='report-swport-netbox'),
    url(r'^swport\?netboxid=(?P<netbox_id>\d+)'
        r'&module=(?P<module_name>[^&]+)$',
        get_report, name='report-swport-module'),

    url(r'^swporttrunk$',
        get_report, name='report-swporttrunk-all'),
    url(r'^swporttrunk\?vlan=(?P<vlan>\d+)$',
        get_report, name='report-swporttrunk-vlan'),
    url(r'^swporttrunk\?vlanid=(?P<vlanid>\d+)$',
        get_report, name='report-swporttrunk-vlanid'),

    url(r'^prefix$',
        get_report, name='report-prefix-all'),
    url(r'^prefix\?prefixid=(?P<prefix_id>\d+)$',
        get_report, name='report-prefix-prefix'),

    url(r'^.*$', get_report, name='report-wildcard')
)

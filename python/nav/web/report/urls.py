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
from django.shortcuts import redirect
from nav.web.report import reports


# Subsystem: Report
# Naming convention: report-<result>-<query>
urlpatterns = patterns('nav.web.report.views',
    url(r'^$', reports.index, name='report-index'),
    url(r'^matrix',
        reports.matrix_report, name='report-matrix'),
    url(r'^reportlist$',
        reports.report_list, name='report-reportlist')
)

# Dummy view
#dummy = lambda reports.handle: *args, **kwargs: None
#dummy = lambda: *args, **kwargs: None
def dummy(request):

    # uri == request.get_full_path()
    # nuri == request.META['QUERY_STRING']
    (report_name, export_delimiter, uri, query_dict) = reports.arg_parsing(request)
    if report_name == 'report':
        return redirect('report-index')
    return reports.make_report(request, report_name, export_delimiter, uri, query_dict)

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

    url(r'^.*$', dummy, name='report-wildcard')
)

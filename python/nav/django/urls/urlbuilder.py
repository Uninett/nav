# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""Django URL configuration"""

# pylint: disable-msg=W0614,W0401

from django.conf.urls.defaults import *

def get_urlpatterns():
    """
    URL patterns for non-Django subsystems

    An alternative to nav.web.urlbuilder for linking from Django apps to
    non-Django parts of NAV in the normal Django way.

    """

    # Dummy view
    dummy = lambda *args, **kwargs: None

    urlpatterns = patterns('',
        # Subsystem: Device History
        url(r'^devicemanagement/$', dummy, name='devicemanagement'),
        url(r'^devicemanagement/\?view_netbox=(?P<netbox_id>\d+)$',
            dummy, name='devicemanagement-history-netbox'),

        # Subsystem: IP Info
        url(r'^ipinfo/$', dummy, name='ipinfo'),
        url(r'^ipinfo/\?ip=(?P<hostname_or_ip>[\w\d._-]+)',
            dummy, name='ipinfo-host'),

        # Subsystem: Maintenance
        url(r'^maintenance/$',
            dummy, name='maintenance'),
        url(r'^maintenance/new\?netbox=(?P<netbox_id>\d+)$',
            dummy, name='maintenance-new-netbox'),
        url(r'^maintenance/new\?service=(?P<service_id>\d+)$',
            dummy, name='maintenance-new-service'),

        # Subsystem: Machine Tracker
#         url(r'^machinetracker/$',
#             dummy, name='machinetracker'),
#         url(r'^machinetracker/swp\?switch=(?P<netbox_sysname>[\w\d._-]+)&module=(?P<module_number>\d+)&port=(?P<port_interface>[\w\d/._-]+)$',
#             dummy, name='machinetracker-swport'),
#         url(r'^machinetracker/swp\?switch=(?P<netbox_sysname>[\w\d._-]+)&port=(?P<port_interface>[\w\d/._-]+)$',
#             dummy, name='machinetracker-swport'),

        # Subsystem: Report
        # Naming convention: report-<result>-<query>
        url(r'^report/org$',
            dummy, name='report-organization-all'),
        url(r'^report/org\?orgid=(?P<organization_id>[^&]+)$',
            dummy, name='report-organization-organization'),

        url(r'^report/type$',
            dummy, name='report-type-all'),
        url(r'^report/type\?typeid=(?P<type_id>\d+)$',
            dummy, name='report-type-type'),

        url(r'^report/netbox$',
            dummy, name='report-netbox-all'),
        url(r'^report/netbox\?roomid=(?P<room_id>[^&]+)$',
            dummy, name='report-netbox-room'),
        url(r'^report/netbox\?catid=(?P<category_id>[\w\d._-]+)$',
            dummy, name='report-netbox-category'),

        url(r'^report/modules$',
            dummy, name='report-modules-all'),
        url(r'^report/modules\?netboxid=(?P<netbox_id>\d+)$',
            dummy, name='report-modules-netbox'),
        url(r'^report/modules\?netboxid=(?P<netbox_id>\d+)&module=(?P<module_number>\d+)$',
            dummy, name='report-modules-module'),

        url(r'^report/gwport$',
            dummy, name='report-gwport-all'),
        url(r'^report/gwport\?netboxid=(?P<netbox_id>\d+)$',
            dummy, name='report-gwport-netbox'),
        url(r'^report/gwport\?netboxid=(?P<netbox_id>\d+)&module=(?P<module_name>[^&]+)$',
            dummy, name='report-gwport-module'),

        url(r'^report/swport$',
            dummy, name='report-swport-all'),
        url(r'^report/swport\?netboxid=(?P<netbox_id>\d+)$',
            dummy, name='report-swport-netbox'),
        url(r'^report/swport\?netboxid=(?P<netbox_id>\d+)&module=(?P<module_name>[^&]+)$',
            dummy, name='report-swport-module'),

        url(r'^report/swporttrunk$',
            dummy, name='report-swporttrunk-all'),
        url(r'^report/swporttrunk\?vlan=(?P<vlan>\d+)$',
            dummy, name='report-swporttrunk-vlan'),
        url(r'^report/swporttrunk\?vlanid=(?P<vlanid>\d+)$',
            dummy, name='report-swporttrunk-vlanid'),

        url(r'^report/prefix$',
            dummy, name='report-prefix-all'),
        url(r'^report/prefix\?prefixid=(?P<prefix_id>\d+)$',
            dummy, name='report-prefix-prefix'),

        # Subsystem: SeedDB
#        url(r'^seeddb/$', dummy, name='seeddb'),
#        url(r'^seeddb/(?P<object_type>\w+)/edit/(?P<object_id>\d+)/$',
#            dummy, name='seeddb-edit-object'),
    )

    return urlpatterns

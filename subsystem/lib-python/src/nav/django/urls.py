# -*- coding: utf-8 -*-
#
# Copyright 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

"""Main Django URL configuration"""

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Give the ipdevinfo namespace to the IP Device Info subsystem
    (r'^ipdevinfo/', include('nav.web.ipdevinfo.urls')),
)

### URL patterns for non-Django subsystems
# An alternative to nav.web.urlbuilder for linking from Django apps to
# non-Django parts of NAV in the normal Django way

# Dummy view
dummy = lambda *args, **kwargs: None

urlpatterns += patterns('',
    # Subsystem: Device History
    url(r'devicemanagement/$', dummy, name='devicemanagement'),
    url(r'devicemanagement/?box=(?P<netbox_id>\d+)&history=1$', dummy,
        name='devicemanagement-history-netbox'),

    # Subsystem: EditDB
    url(r'^editdb/$', dummy, name='editdb'),
    url(r'^editdb/(?P<object_type>\w+)/edit/(?P<object_id>\d+)/$', dummy,
        name='editdb-edit-object'),

    # Subsystem: Maintenance
    url(r'^maintenance/$', dummy, name='maintenance'),
    url(r'^maintenance/new?netbox=(?P<netbox_id>\d+)$', dummy,
        name='maintenance-new-netbox'),
    url(r'^maintenance/new?service=(?P<service_id>\d+)$', dummy,
        name='maintenance-new-service'),

    # Subsystem: Machine Tracker
    url(r'machinetracker/$', dummy, name='machinetracker'),
    url(r'machinetracker/swp?switch=(?P<netbox_sysname>[\w\d._-]+)&module=(?P<module_number>\d+)&port=(?P<port_interface>[\w\d/._-]+)$', dummy,
        name='machinetracker-swport'),

    # Subsystem: Report
    url(r'^report/swporttrunk?vlanid=(?P<vlan_id>\d+)$', dummy,
        name='report-vlan'),
    url(r'^report/netbox?roomid=(?P<room_id>\d+)$', dummy,
        name='report-room'),
    url(r'^report/netbox?catid=(?P<category_id>[\w\d._-]+)$', dummy,
        name='report-category'),
    url(r'^report/org?orgid=(?P<organization_id>[\w\d._-]+)$', dummy,
        name='report-organization'),
    url(r'^report/type?typeid=(?P<type_id>\d+)$', dummy,
        name='report-type'),
    url(r'^report/modules?sysname=(?P<netbox_sysname>[\w\d._-]+)$', dummy,
        name='report-modules'),
    url(r'^report/swport?b1.netboxid=(?P<netbox_id>\d+)$', dummy,
        name='report-swport'),
    url(r'^report/gwport?b1.netboxid=(?P<netbox_id>\d+)$', dummy,
        name='report-gwport'),
    url(r'^report/prefix?prefix.prefixid=(?P<prefix_id>\d+)$', dummy,
        name='report-prefix'),
)

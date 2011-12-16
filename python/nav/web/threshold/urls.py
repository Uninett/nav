#
# Copyright 2011 UNINETT AS
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

from django.conf.urls.defaults import *
from nav.web.threshold.views import index
from nav.web.threshold.views import netbox_search
from nav.web.threshold.views import prepare_bulkset
from nav.web.threshold.views import threshold_edit
from nav.web.threshold.views import box_or_interface
from nav.web.threshold.views import threshold_interface
from nav.web.threshold.views import threshold_delete
from nav.web.threshold.views import threshold_all
from nav.web.threshold.views import threshold_netbox
from nav.web.threshold.views import thresholds_save

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    # List accounts and groups
    url(r'^$', index, name='threshold-index'),
    url(r'^thresholdssave/$', thresholds_save, name='thresholds-save'),
    url(r'^all/$', threshold_all, name='threshold-all'),
    url(r'^exceeded/$', threshold_all, {'exceeded': True}, name='threshold-exceeded'),
    url(r'^preparebulk/$', prepare_bulkset, name='prepare-bulkset'),
    url(r'^choosetype/$', box_or_interface,  name='box-or-interface'),
    url(r'^netboxsearch/$', netbox_search,  name='netbox-search'),
    url(r'^edit/(?P<thresholdid>\d+)/$', threshold_edit, name='threshold-edit'),
    url(r'^delete/(?P<thresholdid>\d+)/$', threshold_delete, name='threshold-delete'),
    url(r'^interface/(?P<interfaceid>\d+)/$', threshold_interface, name='threshold-interface'),
    url(r'^netbox/(?P<netboxid>\d+)/$', threshold_netbox, name='threshold-netbox'),
)

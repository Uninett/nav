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
from nav.web.threshold.views import index, netbox_search, prepare_bulkset
from nav.web.threshold.views import threshold_edit, box_or_interface
from nav.web.threshold.views import threshold_interface, threshold_delete
from nav.web.threshold.views import threshold_all, save_thresholds
from nav.web.threshold.views import threshold_netbox

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('',
    # List accounts and groups
    url(r'^$', index, name='threshold-index'),
    url(r'^all/$', threshold_all, name='threshold-all'),
    url(r'^exceeded/$', threshold_all, {'exceeded': True}, name='threshold-exceeded'),
    url(r'^preparebulk/$', prepare_bulkset, name='prepare-bulkset'),
    url(r'^choosetype/$', box_or_interface,  name='box-or-interface'),
    url(r'^netboxsearch/$', netbox_search,  name='netbox-search'),
    url(r'^savethresholds/$', save_thresholds, name='save-thresholds'),
    url(r'^edit/(?P<thresholdid>\d+)/$', threshold_edit, name='threshold-edit'),
    url(r'^delete/(?P<thresholdid>\d+)/$', threshold_delete, name='threshold-delete'),
    url(r'^interface/(?P<interfaceid>\d+)/$', threshold_interface, name='threshold-interface'),
    url(r'^netbox/(?P<netboxid>\d+)/$', threshold_netbox, name='threshold-netbox'),
)

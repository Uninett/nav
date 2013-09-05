#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Info netboxgroup url configuration"""

from django.conf.urls import url, patterns
from nav.web.info.netboxgroup.views import index, edit_group

urlpatterns = patterns('',
    url(r'^$', index, name='netbox-group'),
    url(r'^edit/(?P<groupid>.+)$', edit_group, name='edit-netbox-group'),
)

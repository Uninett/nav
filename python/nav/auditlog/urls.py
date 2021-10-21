# Copyright (C) 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals, absolute_import

from django.urls import re_path

from .views import AuditlogOverview, AuditlogNetboxDetail


urlpatterns = [
    re_path(r'^$', AuditlogOverview.as_view(), name='auditlog-home'),
    re_path(
        r'^netbox/(?P<netboxid>\d+)$',
        AuditlogNetboxDetail.as_view(),
        name='auditlog-netbox-detail',
    ),
]

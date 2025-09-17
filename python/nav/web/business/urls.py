#
# Copyright (C) 2018 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""URL config for business tool"""

from django.urls import path
from django.urls import re_path
from nav.web.business import views


urlpatterns = [
    path('', views.BusinessView.as_view(), name='business-index'),
    path(
        'device_availability/',
        views.DeviceAvailabilityReport.as_view(),
        name='business-report-device-availability',
    ),
    path(
        'link_availability/',
        views.LinkAvailabilityReport.as_view(),
        name='business-report-link-availability',
    ),
    re_path(
        r'^save_report_subscription',
        views.save_report_subscription,
        name='save-report-subscription',
    ),
    re_path(
        r'^render_report_subscriptions',
        views.render_report_subscriptions,
        name='render-report-subscriptions',
    ),
    re_path(
        r'^remove_report_subscription',
        views.remove_report_subscription,
        name='remove-report-subscription',
    ),
]

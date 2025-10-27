#
# Copyright (C) 2012-2018 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Report backend URL config."""

from django.urls import path, re_path
from nav.web.report import views


# Subsystem: Report
# Naming convention: report-<result>-<query>
urlpatterns = [
    path('', views.index, name='report-index'),
    path('matrix', views.matrix_report, name='report-matrix'),
    re_path(
        r'^matrix/(?P<scope>[^&]+)$', views.matrix_report, name='report-matrix-scope'
    ),
    path('reportlist', views.report_list, name='report-reportlist'),
    path('widget/add/', views.add_report_widget, name='report-add-widget'),
    path(
        'widget/<str:report_name>',
        views.get_report_for_widget,
        name='widget-report-by-name',
    ),
    path('<str:report_name>', views.get_report, name='report-by-name'),
]

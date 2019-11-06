#
# Copyright (C) 2012-2018 Uninett AS
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


from django.conf.urls import url
from nav.web.report import views


# Subsystem: Report
# Naming convention: report-<result>-<query>
urlpatterns = [
    url(r'^$', views.index,
        name='report-index'),
    url(r'^matrix$', views.matrix_report,
        name='report-matrix'),
    url(r'^matrix/(?P<scope>[^&]+)$', views.matrix_report,
        name='report-matrix-scope'),
    url(r'^reportlist$', views.report_list,
        name='report-reportlist'),
    url(r'^(?P<report_name>[^/]+)$', views.get_report,
        name='report-by-name'),
    url(r'^widget/add/', views.add_report_widget,
        name='report-add-widget'),
    url(r'^widget/(?P<report_name>[^/]+)$', views.get_report_for_widget,
        name='widget-report-by-name'),
]

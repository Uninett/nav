#
# Copyright (C) 2009 Uninett AS
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
"""Django URL configuration for webfront"""

from django.urls import re_path
from django.views.generic import RedirectView

from nav.web.webfront import views


urlpatterns = [
    re_path(r'^$', views.index, name='webfront-index'),
    re_path(r'^index/login/', views.login, name='webfront-login'),
    re_path(r'^index/logout/', views.logout, name='webfront-logout'),
    # Dashboard
    re_path(r'^index/dashboard/(?P<did>\d+)', views.index, name='dashboard-index-id'),
    re_path(r'^index/dashboard/add/$', views.add_dashboard, name='add-dashboard'),
    re_path(
        r'^index/dashboard/set_default/(?P<did>\d+)/$',
        views.set_default_dashboard,
        name='set-default-dashboard',
    ),
    re_path(
        r'^index/dashboard/rename/(?P<did>\d+)/$',
        views.rename_dashboard,
        name='rename-dashboard',
    ),
    re_path(
        r'^index/dashboard/delete/(?P<did>\d+)/$',
        views.delete_dashboard,
        name='delete-dashboard',
    ),
    re_path(
        r'^index/dashboard/columns/(?P<did>\d+)/$',
        views.save_dashboard_columns,
        name='save-dashboard-columns',
    ),
    re_path(
        r'^index/dashboard/moveto/(?P<did>\d+)/$',
        views.moveto_dashboard,
        name='moveto-dashboard',
    ),
    re_path(
        r'^index/dashboard/export/(?P<did>\d+)$',
        views.export_dashboard,
        name='export-dashboard',
    ),
    re_path(
        r'^index/dashboard/import$', views.import_dashboard, name='import-dashboard'
    ),
    re_path(r'^index/dashboard/', views.index, name='dashboard-index'),
    re_path(r'^about/', views.about, name='webfront-about'),
    re_path(
        r'^doc/(?P<path>.+)$',
        RedirectView.as_view(url='/static/doc/%(path)s', permanent=True),
    ),
    re_path(
        r'^doc/$', RedirectView.as_view(url='/static/doc/index.html', permanent=True)
    ),
    re_path(
        r'^uploads/(?P<path>.*)$',
        RedirectView.as_view(url='/static/uploads/%(path)s', permanent=True),
    ),
    re_path(r'^toolbox/$', views.toolbox, name='webfront-toolbox'),
    re_path(r'^preferences/$', views.preferences, name='webfront-preferences'),
    re_path(
        r'^preferences/savelinks$',
        views.save_links,
        name='webfront-preferences-savelinks',
    ),
    re_path(
        r'^preferences/changepassword$',
        views.change_password,
        name='webfront-preferences-changepassword',
    ),
    re_path(
        r'^preferences/set_account_preference$',
        views.set_account_preference,
        name='set-account-preference',
    ),
    re_path(r'^qr-code/$', views.qr_code, name='webfront-qr-code'),
]

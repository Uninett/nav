#
# Copyright (C) 2009 Uninett AS
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

from django.conf.urls import url
from django.views.generic import RedirectView

from nav.web.webfront import views


urlpatterns = [
    url(r'^$', views.index, name='webfront-index'),
    url(r'^index/login/', views.login, name='webfront-login'),
    url(r'^index/logout/', views.logout, name='webfront-logout'),
    # Dashboard
    url(r'^index/dashboard/(?P<did>\d+)', views.index, name='dashboard-index-id'),
    url(r'^index/dashboard/add/$', views.add_dashboard, name='add-dashboard'),
    url(
        r'^index/dashboard/set_default/(?P<did>\d+)/$',
        views.set_default_dashboard,
        name='set-default-dashboard',
    ),
    url(
        r'^index/dashboard/rename/(?P<did>\d+)/$',
        views.rename_dashboard,
        name='rename-dashboard',
    ),
    url(
        r'^index/dashboard/delete/(?P<did>\d+)/$',
        views.delete_dashboard,
        name='delete-dashboard',
    ),
    url(
        r'^index/dashboard/columns/(?P<did>\d+)/$',
        views.save_dashboard_columns,
        name='save-dashboard-columns',
    ),
    url(
        r'^index/dashboard/moveto/(?P<did>\d+)/$',
        views.moveto_dashboard,
        name='moveto-dashboard',
    ),
    url(
        r'^index/dashboard/export/(?P<did>\d+)$',
        views.export_dashboard,
        name='export-dashboard',
    ),
    url(r'^index/dashboard/import$', views.import_dashboard, name='import-dashboard'),
    url(r'^index/dashboard/', views.index, name='dashboard-index'),
    url(r'^about/', views.about, name='webfront-about'),
    url(
        r'^doc/(?P<path>.+)$',
        RedirectView.as_view(url='/static/doc/%(path)s', permanent=True),
    ),
    url(r'^doc/$', RedirectView.as_view(url='/static/doc/index.html', permanent=True)),
    url(
        r'^uploads/(?P<path>.*)$',
        RedirectView.as_view(url='/static/uploads/%(path)s', permanent=True),
    ),
    url(r'^toolbox/$', views.toolbox, name='webfront-toolbox'),
    url(r'^preferences/$', views.preferences, name='webfront-preferences'),
    url(
        r'^preferences/savelinks$',
        views.save_links,
        name='webfront-preferences-savelinks',
    ),
    url(
        r'^preferences/changepassword$',
        views.change_password,
        name='webfront-preferences-changepassword',
    ),
    url(
        r'^preferences/setcolumns$',
        views.set_widget_columns,
        name='webfront-preferences-setwidgetcolumns',
    ),
    url(
        r'^preferences/set_account_preference$',
        views.set_account_preference,
        name='set-account-preference',
    ),
]

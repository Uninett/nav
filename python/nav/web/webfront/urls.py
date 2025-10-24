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

from django.urls import path, re_path
from django.views.generic import RedirectView

from nav.web.webfront import views


urlpatterns = [
    path('', views.index, name='webfront-index'),
    path('index/login/', views.login, name='webfront-login'),
    path(
        'index/audit-logging-modal/',
        views.audit_logging_modal,
        name='webfront-audit-logging-modal',
    ),
    path('index/logout/', views.logout, name='webfront-logout'),
    # Dashboard
    path('index/dashboard/<int:did>/', views.index, name='dashboard-index-id'),
    path(
        'index/dashboard/toggle-shared/<int:did>/',
        views.toggle_dashboard_shared,
        name='dashboard-toggle-shared',
    ),
    path(
        'index/dashboard/toggle-subscribe/<int:did>/',
        views.toggle_subscribe,
        name='dashboard-toggle-subscribe',
    ),
    path(
        'index/dashboard/search/modal/',
        views.dashboard_search_modal,
        name='dashboard-search-modal',
    ),
    path('index/dashboard/search/', views.dashboard_search, name='dashboard-search'),
    path('index/dashboard/add/', views.add_dashboard, name='add-dashboard'),
    path(
        'index/dashboard/set_default/<int:did>/',
        views.set_default_dashboard,
        name='set-default-dashboard',
    ),
    path(
        'index/dashboard/rename/<int:did>/',
        views.rename_dashboard,
        name='rename-dashboard',
    ),
    path(
        'index/dashboard/delete/<int:did>/',
        views.delete_dashboard,
        name='delete-dashboard',
    ),
    path(
        'index/dashboard/columns/<int:did>/',
        views.save_dashboard_columns,
        name='save-dashboard-columns',
    ),
    path(
        'index/dashboard/moveto/<int:did>/',
        views.moveto_dashboard,
        name='moveto-dashboard',
    ),
    path(
        'index/dashboard/export/<int:did>',
        views.export_dashboard,
        name='export-dashboard',
    ),
    path('index/dashboard/import', views.import_dashboard, name='import-dashboard'),
    path(
        'index/dashboard/importmodal',
        views.import_dashboard_modal,
        name='import-dashboard-modal',
    ),
    path('index/dashboard/', views.index, name='dashboard-index'),
    path('about/', views.about, name='webfront-about'),
    path(
        'doc/<path:path>',
        RedirectView.as_view(url='/static/doc/%(path)s', permanent=True),
    ),
    path('doc/', RedirectView.as_view(url='/static/doc/index.html', permanent=True)),
    re_path(
        r'^uploads/(?P<path>.*)$',
        RedirectView.as_view(url='/static/uploads/%(path)s', permanent=True),
    ),
    path('toolbox/', views.toolbox, name='webfront-toolbox'),
    path('preferences/', views.preferences, name='webfront-preferences'),
    path(
        'preferences/savelinks',
        views.save_links,
        name='webfront-preferences-savelinks',
    ),
    path(
        'preferences/changepassword',
        views.change_password,
        name='webfront-preferences-changepassword',
    ),
    path(
        'preferences/set_account_preference',
        views.set_account_preference,
        name='set-account-preference',
    ),
    path('qr-code/', views.qr_code, name='webfront-qr-code'),
]

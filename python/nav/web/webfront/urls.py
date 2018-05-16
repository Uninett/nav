#
# Copyright (C) 2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django URL configuration for webfront"""

from django.conf.urls import url, patterns

urlpatterns = patterns(
    'nav.web.webfront.views',
    url(r'^$', 'index', name='webfront-index'),
    url(r'^index/login/', 'login', name='webfront-login'),
    url(r'^index/logout/', 'logout', name='webfront-logout'),

    # Dashboard
    url(r'^index/dashboard/(?P<did>\d+)', 'index', name='dashboard-index-id'),
    url(r'^index/dashboard/add/$', 'add_dashboard', name='add-dashboard'),
    url(r'^index/dashboard/set_default/(?P<did>\d+)/$', 'set_default_dashboard',
        name='set-default-dashboard'),
    url(r'^index/dashboard/rename/(?P<did>\d+)/$', 'rename_dashboard',
        name='rename-dashboard'),
    url(r'^index/dashboard/delete/(?P<did>\d+)/$', 'delete_dashboard',
        name='delete-dashboard'),
    url(r'^index/dashboard/columns/(?P<did>\d+)/$', 'save_dashboard_columns',
        name='save-dashboard-columns'),
    url(r'^index/dashboard/moveto/(?P<did>\d+)/$', 'moveto_dashboard',
        name='moveto-dashboard'),
    url(r'^index/dashboard/export/(?P<did>\d+)$', 'export_dashboard',
        name='export-dashboard'),
    url(r'^index/dashboard/import$', 'import_dashboard',
        name='import-dashboard'),
    url(r'^index/dashboard/', 'index', name='dashboard-index'),

    url(r'^about/', 'about', name='webfront-about'),
    url(r'^toolbox/$', 'toolbox', name='webfront-toolbox'),
    url(r'^preferences/$', 'preferences', name='webfront-preferences'),
    url(r'^preferences/savelinks$', 'save_links',
        name='webfront-preferences-savelinks'),
    url(r'^preferences/changepassword$', 'change_password',
        name='webfront-preferences-changepassword'),
    url(r'^preferences/setcolumns$', 'set_widget_columns',
        name='webfront-preferences-setwidgetcolumns'),
    url(r'^preferences/set_account_preference$', 'set_account_preference',
        name='set-account-preference'),
)

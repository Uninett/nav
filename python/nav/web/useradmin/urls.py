# -*- coding: utf-8 -*-
#
# Copyright 2008, 2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
"""Django URL config for useradmin"""

from django.urls import re_path
from nav.web.useradmin import views

# The patterns are relative to the base URL of the subsystem
urlpatterns = [
    # List accounts and groups
    re_path(r'^$', views.account_list, name='useradmin'),
    re_path(r'^accounts/$', views.account_list, name='useradmin-account_list'),
    re_path(r'^groups/$', views.group_list, name='useradmin-group_list'),
    # Edit/Create accounts
    re_path(r'^account/new/$', views.account_detail, name='useradmin-account_new'),
    re_path(
        r'^account/(?P<account_id>\d+)/$',
        views.account_detail,
        name='useradmin-account_detail',
    ),
    # Deletion
    re_path(
        r'^account/(?P<account_id>\d+)/delete/$',
        views.account_delete,
        name='useradmin-account_delete',
    ),
    re_path(
        r'^account/(?P<account_id>\d+)/remove/group/(?P<group_id>\d+)/$',
        views.account_group_remove,
        name='useradmin-account_group_remove',
    ),
    re_path(
        r'^account/(?P<account_id>\d+)/remove/org/(?P<org_id>[^\\]+)/$',
        views.account_organization_remove,
        name='useradmin-account_organization_remove',
    ),
    # Edit/Create groups
    re_path(r'^group/new/$', views.group_detail, name='useradmin-group_new'),
    re_path(
        r'^group/(?P<group_id>\d+)/$', views.group_detail, name='useradmin-group_detail'
    ),
    re_path(
        r'^group/(?P<group_id>\d+)/delete/$',
        views.group_delete,
        name='useradmin-group_delete',
    ),
    re_path(
        r'^group/(?P<group_id>\d+)/remove/account/(?P<account_id>\d+)/$',
        views.group_account_remove,
        name='useradmin-group_account_remove',
    ),
    re_path(
        r'^group/(?P<group_id>\d+)/remove/privilege/(?P<privilege_id>\d+)/$',
        views.group_privilege_remove,
        name='useradmin-group_privilege_remove',
    ),
    # Manage tokens
    re_path(r'^tokens/$', views.TokenList.as_view(), name='useradmin-token_list'),
    re_path(
        r'^tokens/create/$', views.TokenCreate.as_view(), name='useradmin-token_create'
    ),
    re_path(
        r'^tokens/edit/(?P<pk>\d+)/$',
        views.TokenEdit.as_view(),
        name='useradmin-token_edit',
    ),
    re_path(
        r'^tokens/detail/(?P<pk>\d+)/$',
        views.TokenDetail.as_view(),
        name='useradmin-token_detail',
    ),
    re_path(
        r'^tokens/delete/(?P<pk>\d+)/$',
        views.TokenDelete.as_view(),
        name='useradmin-token_delete',
    ),
    re_path(
        r'^tokens/expire/(?P<pk>\d+)/$',
        views.token_expire,
        name='useradmin-token_expire',
    ),
]

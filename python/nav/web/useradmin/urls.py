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

from django.urls import path
from django.urls import re_path
from nav.web.useradmin import views

# The patterns are relative to the base URL of the subsystem
urlpatterns = [
    # List accounts and groups
    path('', views.account_list, name='useradmin'),
    path('accounts/', views.account_list, name='useradmin-account_list'),
    path('groups/', views.group_list, name='useradmin-group_list'),
    # Edit/Create accounts
    path('account/new/', views.account_detail, name='useradmin-account_new'),
    path(
        'account/<int:account_id>/',
        views.account_detail,
        name='useradmin-account_detail',
    ),
    # Deletion
    path(
        'account/<int:account_id>/delete/',
        views.account_delete,
        name='useradmin-account_delete',
    ),
    path(
        'account/<int:account_id>/remove/group/<int:group_id>/',
        views.account_group_remove,
        name='useradmin-account_group_remove',
    ),
    re_path(
        r'^account/(?P<account_id>\d+)/remove/org/(?P<org_id>[^\\]+)/$',
        views.account_organization_remove,
        name='useradmin-account_organization_remove',
    ),
    # Edit/Create groups
    path('group/new/', views.group_detail, name='useradmin-group_new'),
    path('group/<int:group_id>/', views.group_detail, name='useradmin-group_detail'),
    path(
        'group/<int:group_id>/delete/',
        views.group_delete,
        name='useradmin-group_delete',
    ),
    path(
        'group/<int:group_id>/remove/account/<int:account_id>/',
        views.group_account_remove,
        name='useradmin-group_account_remove',
    ),
    path(
        'group/<int:group_id>/remove/privilege/<int:privilege_id>/',
        views.group_privilege_remove,
        name='useradmin-group_privilege_remove',
    ),
    # Manage tokens
    path('tokens/', views.TokenList.as_view(), name='useradmin-token_list'),
    path('tokens/create/', views.TokenCreate.as_view(), name='useradmin-token_create'),
    path(
        'tokens/edit/<int:pk>/',
        views.TokenEdit.as_view(),
        name='useradmin-token_edit',
    ),
    path(
        'tokens/detail/<int:pk>/',
        views.TokenDetail.as_view(),
        name='useradmin-token_detail',
    ),
    path(
        'tokens/delete/<int:pk>/',
        views.TokenDelete.as_view(),
        name='useradmin-token_delete',
    ),
    path(
        'tokens/expire/<int:pk>/',
        views.token_expire,
        name='useradmin-token_expire',
    ),
    # Manage JWT tokens
    path('jwt_tokens/', views.JWTList.as_view(), name='useradmin-jwt_list'),
    path('jwt_tokens/create/', views.JWTCreate.as_view(), name='useradmin-jwt_create'),
    path(
        'jwt_tokens/edit/<int:pk>/',
        views.JWTEdit.as_view(),
        name='useradmin-jwt_edit',
    ),
    path(
        'jwt_tokens/detail/<int:pk>/',
        views.JWTDetail.as_view(),
        name='useradmin-jwt_detail',
    ),
    path(
        'jwt_tokens/delete/<int:pk>/',
        views.JWTDelete.as_view(),
        name='useradmin-jwt_delete',
    ),
    path(
        'jwt_tokens/expire/<int:pk>/',
        views.jwt_revoke,
        name='useradmin-jwt_revoke',
    ),
    path(
        'jwt_tokens/recreate/<int:pk>/',
        views.jwt_recreate,
        name='useradmin-jwt_recreate',
    ),
]

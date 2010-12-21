# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Authors: Thomas Adamcik <thomas.adamcik@uninett.no>
#
"""Django URL config for useradmin"

# pylint: disable-msg=W0614,W0401

from django.conf.urls.defaults import *

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('nav.web.useradmin.views',
    # List accounts and groups
    url(r'^$', 'account_list', name='useradmin'),
    url(r'^accounts/$', 'account_list', name='useradmin-account_list'),
    url(r'^groups/$', 'group_list', name='useradmin-group_list'),

    # Edit/Create accounts
    url(r'^account/new/$', 'account_detail', name='useradmin-account_new'),
    url(r'^account/(?P<account_id>\d+)/$', 'account_detail', name='useradmin-account_detail'),

    # Deletion
    url(r'^account/(?P<account_id>\d+)/delete/$', 'account_delete', name='useradmin-account_delete'),
    url(r'^account/(?P<account_id>\d+)/remove/group/(?P<group_id>\d+)/$', 'account_group_remove', name='useradmin-account_group_remove'),
    url(r'^account/(?P<account_id>\d+)/remove/org/(?P<org_id>[^\\]+)/$', 'account_organization_remove', name='useradmin-account_organization_remove'),

    # Edit/Create groups
    url(r'^group/new/$', 'group_detail', name='useradmin-group_new'),
    url(r'^group/(?P<group_id>\d+)/$', 'group_detail', name='useradmin-group_detail'),

    url(r'^group/(?P<group_id>\d+)/delete/$', 'group_delete', name='useradmin-group_delete'),
    url(r'^group/(?P<group_id>\d+)/remove/account/(?P<account_id>\d+)/$', 'group_account_remove', name='useradmin-group_account_remove'),
    url(r'^group/(?P<group_id>\d+)/remove/privilege/(?P<privilege_id>\d+)/$', 'group_privilege_remove', name='useradmin-group_privilege_remove'),
)

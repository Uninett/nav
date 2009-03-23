# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 UNINETT AS
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

"""Utility methods for django used in NAV"""

from copy import copy
from django.http import HttpResponseForbidden

from nav.models.profiles import Account

# Admingroup is identified by having id/primary key 1.
ADMINGROUP = 1

def get_account(request):
    """Extracts users login from sessionvariables and looks up the
    corresponding account in the database
    """

    return Account.objects.get(login=request._req.session['user'].login)

def is_admin(account):
    """Check if user is a member of the administrator group"""
    return account.accountgroup_set.filter(pk=ADMINGROUP).count() > 0;

def permission_required(function):
    """Decorator to check if user have access"""
    def _check_permission(request, *args, **kwargs):
        account = get_account(request)
        if account.has_perm('web_access', request.path):
            return function(request, *args, **kwargs)
        else:
            # FIXME better 403 handling
            return HttpResponseForbidden('<h1>403 Forbidden</h1><p>You do not have access to this page</p>')
    return _check_permission

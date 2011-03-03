# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 UNINETT AS
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
from django.db.models.fields import FieldDoesNotExist

from nav.models.profiles import Account, AccountGroup

def get_account(request):
    """Tries to fetch account from request object. If it's not found we look it
    up in the database.
    """
    try:
        account = request.account
    except AttributeError:
        account = Account.objects.get(
            login=request._req.session['user']['login'])
        request.account = account
    return account

def sudoer(req):
    if hasattr(req, 'session') and req.session.has_key('user'):
        user = req.session['user']
        if user.has_key('sudoer'):
            account = Account.objects.get(id=user['sudoer']['id'])
            return account
    return None

def is_admin(account):
    """Check if user is a member of the administrator group"""
    return account.accountgroup_set.filter(
        pk=AccountGroup.ADMIN_GROUP).count() > 0;

def permission_required(function):
    """Decorator to check if user have access"""
    def _check_permission(request, *args, **kwargs):
        account = get_account(request)
        if account.has_perm('web_access', request.path):
            return function(request, *args, **kwargs)
        else:
            # FIXME better 403 handling
            return HttpResponseForbidden(
                '<h1>403 Forbidden</h1>'
                '<p>You do not have access to this page</p>')
    return _check_permission

def get_verbose_name(model, lookup):
    """Verbose name introspection of ORM models.
       Parameters:
         - model: the django model
         - lookup: name of the field to find verbose name of.

       Foreign key lookups is supported, ie. "othermodel__otherfield"
    """
    if '__' not in lookup:
        return model._meta.get_field(lookup).verbose_name

    foreign_key, lookup = lookup.split('__', 1)
    try:
        foreign_model = model._meta.get_field(foreign_key).rel.to
        return get_verbose_name(foreign_model, lookup)
    except FieldDoesNotExist:
        pass

    related = model._meta.get_all_related_objects()
    related += model._meta.get_all_related_many_to_many_objects()
    for obj in related:
        if obj.get_accessor_name() == foreign_key:
            return get_verbose_name(obj.model, lookup)

    raise FieldDoesNotExist

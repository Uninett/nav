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

import django
from django.http import HttpResponseForbidden
from django.db.models.fields import FieldDoesNotExist

from nav.models.profiles import Account, AccountGroup

def get_request_body(request):
    """ Function for retrieving the request body
    https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.body

    :param request: request
    :return: request body
    """
    if django.VERSION >= (1, 4):
        return request.body
    else:
        return request.raw_post_data


def get_account(request):
    """Returns the account associated with the request"""
    return request.account


def is_admin(account):
    """Check if user is a member of the administrator group"""
    return account.accountgroup_set.filter(
        pk=AccountGroup.ADMIN_GROUP).count() > 0


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

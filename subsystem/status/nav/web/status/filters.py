# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#

from nav.models.profiles import Account
from nav.models.manage import Netbox, Organization, Category

class _Filter(object):
    '''Base class for filters.

    Fields:
        available -- A list of all the available objects for this filter.

    The objects in the available list are simple dictionaries with three fields:
        id       -- "Primary key"
        name     -- The visual identification.
        selected -- If it's selected or not.
    '''
    available = []

    def set_available(self, data):
        self.available = data

    def set_selected(self, selected):
        for object in available:
            if object['id'] in selected:
                object['selected'] = True

    def filter(self):
        ret = []
        for object in available:
            if 'selected' in object and object['selected']:
                ret.append(object['id'])
        return ret

_organization_cache = None
class OrganizationFilter(_Filter):
    def set_available(self, account):
        # Check if user is admin.
        # Admins have access to all organizations
        groups = account.accountgroup_set.all()
        is_admin = False
        for g in groups:
            if g.is_admin_group():
                is_admin = True
                break

        global _organization_cahce
        if not _organization_cache:
            if is_admin:
                organizations = account.organizations.all()
            else:
                organizations = Organization.objects.all()
            _organization_cache = organizations

        for org in _organization_cache:
            self.available.append({
                'id': org.id,
                'name': org.id,
                'selected': False,
            })

_category_cache = None
class CategoryFilter(_Filter):
    def __init__(self):
        global _category_cache
        if not _category_cache:
            _category_cache = Category.objects.all()

        for cat in _category_cache:
            self.available.append({
                'id': cat.id,
                'name': cat.id,
                'selected': False,
            })

class StateFilter(_Filter):
    def __init__(self):
        states = Netbox.UP_CHOICES
        for state in states:
            self.available.append({
                'id': state[0],
                'name': state[1],
                'selected': False,
            })

class ServiceFilter(_Filter):
    def __init__(self):
        # Read from file and junk
        pass

# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 UNINETT AS
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

from django.core.urlresolvers import reverse

from nav.models.manage import Netbox, Room, Organization

from nav.web.seeddb.forms.move import NetboxMoveForm, RoomMoveForm
from nav.web.seeddb.forms.move import OrganizationMoveForm
from nav.web.seeddb.utils.move import move

TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def netbox_move(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('IP Devices', reverse('seeddb-netbox'))],
        'tab_template': 'seeddb/tabs_netbox.html',
        'active': {'netbox': True},
    }
    return move(request, Netbox, NetboxMoveForm, 'seeddb-netbox',
        title_attr='sysname',
        extra_context=extra)

def room_move(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
        'active': {'room': True},
    }
    return move(request, Room, RoomMoveForm, 'seeddb-room',
        extra_context=extra)

def organization_move(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [
            ('Organization', reverse('seeddb-organization'))],
        'tab_template': 'seeddb/tabs_organization.html',
        'active': {'organization': True},
    }
    return move(request, Organization, OrganizationMoveForm,
        'seeddb-organization',
        extra_context=extra)

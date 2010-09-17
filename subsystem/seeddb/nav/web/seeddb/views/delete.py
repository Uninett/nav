# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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

from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization, Device
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.service import Service

from nav.web.seeddb.utils.delete import render_delete

NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def room_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
    }
    return render_delete(request, Room, 'seeddb-room',
        extra_context=extra)

def location_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Location', reverse('seeddb-location'))],
        'tab_template': 'seeddb/tabs_location.html',
    }
    return render_delete(request, Location, 'seeddb-location',
        extra_context=extra)

def organization_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Organization', reverse('seeddb-organization'))],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_delete(request, Organization, 'seeddb-organization',
        extra_context=extra)

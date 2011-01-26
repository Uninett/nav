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

from nav.bulkparse import NetboxBulkParser, RoomBulkParser, LocationBulkParser, OrgBulkParser
from nav.bulkimport import NetboxImporter, RoomImporter, LocationImporter, OrgImporter

from nav.web.seeddb.utils.bulk import render_bulkimport

TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def netbox_bulk(request):
    extra = {
        'active': {'netbox': True},
        'title': TITLE_DEFAULT + ' - IP Devices',
        'navpath': NAVPATH_DEFAULT + [('IP Devices', None)],
        'tab_template': 'seeddb/tabs_netbox.html',
    }
    return render_bulkimport(
            request, NetboxBulkParser, NetboxImporter,
            'seeddb-netbox',
            extra_context=extra)

def room_bulk(request):
    extra = {
        'active': {'room': True},
        'title': TITLE_DEFAULT + ' - Room',
        'navpath': NAVPATH_DEFAULT + [('Room', None)],
        'tab_template': 'seeddb/tabs_room.html',
    }
    return render_bulkimport(
        request, RoomBulkParser, RoomImporter,
        'seeddb-room',
        extra_context=extra)

def location_bulk(request):
    extra = {
        'active': {'location': True},
        'title': TITLE_DEFAULT + ' - Location',
        'navpath': NAVPATH_DEFAULT + [('Location', None)],
        'tab_template': 'seeddb/tabs_location.html',
    }
    return render_bulkimport(
        request, LocationBulkParser, LocationImporter,
        'seeddb-location',
        extra_context=extra)

def organization_bulk(request):
    extra = {
        'active': {'organization': True},
        'title': TITLE_DEFAULT + ' - Organization',
        'navpath': NAVPATH_DEFAULT + [('Organization', None)],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_bulkimport(
        request, OrgBulkParser, OrgImporter,
        'seeddb-organization',
        extra_context=extra)

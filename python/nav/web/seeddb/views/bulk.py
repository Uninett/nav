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

from nav.bulkparse import NetboxBulkParser, RoomBulkParser, LocationBulkParser
from nav.bulkparse import OrgBulkParser, UsageBulkParser, NetboxTypeBulkParser
from nav.bulkparse import VendorBulkParser, SubcatBulkParser, CablingBulkParser
from nav.bulkparse import PatchBulkParser, ServiceBulkParser
from nav.bulkimport import NetboxImporter, RoomImporter, LocationImporter
from nav.bulkimport import OrgImporter, UsageImporter, NetboxTypeImporter
from nav.bulkimport import VendorImporter, SubcatImporter, CablingImporter
from nav.bulkimport import PatchImporter, ServiceImporter

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

def service_bulk(request):
    extra = {
        'active': {'service': True},
        'title': TITLE_DEFAULT + ' - Service',
        'navpath': NAVPATH_DEFAULT + [('Service', None)],
        'tab_template': 'seeddb/tabs_service.html',
    }
    return render_bulkimport(
            request, ServiceBulkParser, ServiceImporter,
            'seeddb-service',
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

def usage_bulk(request):
    extra = {
        'active': {'usage': True},
        'title': TITLE_DEFAULT + ' - Usage',
        'navpath': NAVPATH_DEFAULT + [('Usage', None)],
        'tab_template': 'seeddb/tabs_usage.html',
    }
    return render_bulkimport(
        request, UsageBulkParser, UsageImporter,
        'seeddb-usage',
        extra_context=extra)

def netboxtype_bulk(request):
    extra = {
        'active': {'type': True},
        'title': TITLE_DEFAULT + ' - Type',
        'navpath': NAVPATH_DEFAULT + [('Type', None)],
        'tab_template': 'seeddb/tabs_type.html',
    }
    return render_bulkimport(
        request, NetboxTypeBulkParser, NetboxTypeImporter,
        'seeddb-type',
        extra_context=extra)

def vendor_bulk(request):
    extra = {
        'active': {'vendor': True},
        'title': TITLE_DEFAULT + ' - Vendor',
        'navpath': NAVPATH_DEFAULT + [('Vendor', None)],
        'tab_template': 'seeddb/tabs_vendor.html',
    }
    return render_bulkimport(
        request, VendorBulkParser, VendorImporter,
        'seeddb-vendor',
        extra_context=extra)

def subcategory_bulk(request):
    extra = {
        'active': {'subcategory': True},
        'title': TITLE_DEFAULT + ' - Subcategory',
        'navpath': NAVPATH_DEFAULT + [('Subcategory', None)],
        'tab_template': 'seeddb/tabs_subcategory.html',
    }
    return render_bulkimport(
        request, SubcatBulkParser, SubcatImporter,
        'seeddb-subcategory',
        extra_context=extra)

def cabling_bulk(request):
    extra = {
        'active': {'cabling': True},
        'title': TITLE_DEFAULT + ' - Cabling',
        'navpath': NAVPATH_DEFAULT + [('Cabling', None)],
        'tab_template': 'seeddb/tabs_cabling.html',
    }
    return render_bulkimport(
        request, CablingBulkParser, CablingImporter,
        'seeddb-cabling',
        extra_context=extra)

def patch_bulk(request):
    extra = {
        'active': {'patch': True},
        'title': TITLE_DEFAULT + ' - Patch',
        'navpath': NAVPATH_DEFAULT + [('Patch', None)],
        'tab_template': 'seeddb/tabs_patch.html',
    }
    return render_bulkimport(
        request, PatchBulkParser, PatchImporter,
        'seeddb-patch',
        extra_context=extra)

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

from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix, Device
from nav.models.service import Service

from nav.web.seeddb.utils.delete import render_delete

NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]
SEEDDB_EDITABLE_MODELS = (
    Netbox, NetboxType, Room, Location, Organization, Device, Usage, Vendor,
    Subcategory, Vlan, Prefix, Service
)

def netbox_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('IP Devices', reverse('seeddb-netbox'))],
        'tab_template': 'seeddb/tabs_netbox.html',
        'active': {'netbox': True},
    }
    return render_delete(request, Netbox, 'seeddb-netbox',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def service_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Service', reverse('seeddb-service'))],
        'tab_template': 'seeddb/tabs_service.html',
        'active': {'service': True},
    }
    return render_delete(request, Service, 'seeddb-service',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def room_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
        'active': {'room': True},
    }
    return render_delete(request, Room, 'seeddb-room',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def location_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Location', reverse('seeddb-location'))],
        'tab_template': 'seeddb/tabs_location.html',
        'active': {'location': True},
    }
    return render_delete(request, Location, 'seeddb-location',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def organization_delete(request):
    navpath = NAVPATH_DEFAULT + [('Organization',
        reverse('seeddb-organization'))]
    extra = {
        'navpath': navpath,
        'tab_template': 'seeddb/tabs_organization.html',
        'active': {'organization': True},
    }
    return render_delete(request, Organization, 'seeddb-organization',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def usage_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Usage', reverse('seeddb-usage'))],
        'tab_template': 'seeddb/tabs_usage.html',
        'active': {'usage': True},
    }
    return render_delete(request, Usage, 'seeddb-usage',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def netboxtype_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Usage', reverse('seeddb-usage'))],
        'tab_template': 'seeddb/tabs_usage.html',
        'active': {'type': True},
    }
    return render_delete(request, NetboxType, 'seeddb-type',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def vendor_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Vendor', reverse('seeddb-vendor'))],
        'tab_template': 'seeddb/tabs_vendor.html',
        'active': {'vendor': True},
    }
    return render_delete(request, Vendor, 'seeddb-vendor',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def subcategory_delete(request):
    navpath = NAVPATH_DEFAULT + [('Subcategory', reverse('seeddb-subcategory'))]
    extra = {
        'navpath': navpath,
        'tab_template': 'seeddb/tabs_subcategory.html',
        'active': {'subcategory': True},
    }
    return render_delete(request, Subcategory, 'seeddb-subcategory',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def cabling_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Cabling', reverse('seeddb-cabling'))],
        'tab_template': 'seeddb/tabs_cabling.html',
        'active': {'cabling': True},
    }
    return render_delete(request, Cabling, 'seeddb-cabling',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def patch_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Patch', reverse('seeddb-patch'))],
        'tab_template': 'seeddb/tabs_patch.html',
        'active': {'patch': True},
    }
    return render_delete(request, Patch, 'seeddb-patch',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

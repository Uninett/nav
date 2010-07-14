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
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list
from django.views.generic.create_update import update_object

from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization, Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.service import Service
from nav.web.message import new_message, Messages

from nav.web.seeddb.forms import *
from nav.web.seeddb.utils import *
from nav.web.seeddb.utils.list import *

TITLE_DEFAULT = 'NAV - Seed Database'
NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def index(request):
    return render_to_response(
        'seeddb/index.html',
        {
            'title': TITLE_DEFAULT,
            'navpath': [('Home', '/'), ('Seed DB', None)],
            'active': {'index': True},
        },
        RequestContext(request)
    )

def netbox_list(request):
    list = NetboxList(request)
    return list()

def service_list(request):
    qs = Service.objects.all()
    value_list = ('netbox__sysname', 'handler', 'version')
    extra = {
        'title': TITLE_DEFAULT + ' - Services',
        'caption': 'Services',
        'navpath': NAVPATH_DEFAULT + [('Services', None)],
        'tab_template': 'seeddb/tabs_service.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-service-edit', extra_context=extra)

def room_list(request):
    if request.method == 'POST':
        if request.POST.get('move'):
            return room_move(request)
        if request.POST.get('delete'):
            return room_delete(request)

    list = RoomList(request)
    return list()

def room_edit(request, room_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Rooms', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
    }
    return render_seeddb_edit(request, Room, RoomForm,
        room_id, extra_context=extra)

def location_list(request):
    qs = Location.objects.all()
    value_list = ('id', 'description')
    extra = {
        'title': TITLE_DEFAULT + ' - Locations',
        'caption': 'Locations',
        'navpath': NAVPATH_DEFAULT + [('Locations', None)],
        'tab_template': 'seeddb/tabs_location.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-location-edit', extra_context=extra)

def location_edit(request, location_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Locations', None)],
        'tab_template': 'seeddb/tabs_location.html',
    }
    return render_seeddb_edit(request, Location, LocationForm,
        location_id, extra_context=extra)

def organization_list(request):
    qs = Organization.objects.all()
    value_list = (
        'id', 'parent', 'description', 'optional_1', 'optional_2',
        'optional_3')
    extra = {
        'title': TITLE_DEFAULT + ' - Organizations',
        'caption': 'Organizations',
        'navpath': NAVPATH_DEFAULT + [('Organizations', None)],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-organization-edit', extra_context=extra)

def organization_edit(request, organization_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Organizations', reverse('seeddb-organization'))],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_seeddb_edit(request, Organization, OrganizationForm,
        organization_id, extra_context=extra)

def usage_list(request):
    qs = Usage.objects.all()
    value_list = ('id', 'description')
    extra = {
        'title': TITLE_DEFAULT + ' - Usage categories',
        'caption': 'Usage categories',
        'navpath': NAVPATH_DEFAULT + [('Usage categories', None)],
        'tab_template': 'seeddb/tabs_usage.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-usage-edit', extra_context=extra)

def usage_edit(request, usage_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Usage categories', reverse('seeddb-usage'))],
        'tab_template': 'seeddb/tabs_usage.html',
    }
    return render_seeddb_edit(request, Usage, UsageForm,
        usage_id, extra_context=extra)

def type_list(request):
    qs = NetboxType.objects.all()
    value_list = (
        'name', 'vendor', 'description', 'sysobjectid', 'frequency', 'cdp',
        'tftp')
    extra = {
        'title': TITLE_DEFAULT + ' - Types',
        'caption': 'Types',
        'navpath': NAVPATH_DEFAULT + [('Types', None)],
        'tab_template': 'seeddb/tabs_type.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-type-edit', extra_context=extra)

def type_edit(request, type_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Types', reverse('seeddb-type'))],
        'tab_template': 'seeddb/tabs_type.html',
    }
    return render_seeddb_edit(request, NetboxType, NetboxTypeForm,
        type_id, title_attr='name', extra_context=extra)

def vendor_list(request):
    qs = Vendor.objects.all()
    value_list = ('id',)
    extra = {
        'title': TITLE_DEFAULT + ' - Vendors',
        'caption': 'Vendors',
        'navpath': NAVPATH_DEFAULT + [('Vendors', None)],
        'tab_template': 'seeddb/tabs_vendor.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-vendor-edit', extra_context=extra)

def vendor_edit(request, vendor_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Vendors', reverse('seeddb-vendor'))],
        'tab_template': 'seeddb/tabs_vendor.html',
    }
    return render_seeddb_edit(request, Vendor, VendorForm,
        vendor_id, extra_context=extra)

def subcategory_list(request):
    qs = Subcategory.objects.all()
    value_list = ('id', 'category', 'description')
    extra = {
        'title': TITLE_DEFAULT + ' - Subcategories',
        'caption': 'Subcategories',
        'navpath': NAVPATH_DEFAULT + [('Subcategories', None)],
        'tab_template': 'seeddb/tabs_subcategory.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-subcategory-edit', extra_context=extra)

def subcategory_edit(request, subcategory_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Subcategories', reverse('seeddb-subcategory'))],
        'tab_template': 'seeddb/tabs_subcategory.html',
    }
    return render_seeddb_edit(request, Subcategory, SubcategoryForm,
        subcategory_id, extra_context=extra)

def vlan_list(request):
    qs = Vlan.objects.all()
    value_list = ('id', 'vlan', 'net_type', 'organization', 'usage', 'net_ident', 'description')
    extra = {
        'title': TITLE_DEFAULT + ' - Vlan',
        'caption': 'Vlan',
        'navpath': NAVPATH_DEFAULT + [('Vlan', None)],
        'tab_template': 'seeddb/tabs_vlan.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-vlan-edit', extra_context=extra)

def prefix_list(request):
    qs = Prefix.objects.filter(vlan__net_type__edit=True)
    value_list = (
        'net_address', 'vlan__net_type', 'vlan__organization',
        'vlan__net_ident', 'vlan__usage', 'vlan__description', 'vlan__vlan')
    extra = {
        'title': TITLE_DEFAULT + ' - Prefix',
        'caption': 'Prefix',
        'navpath': NAVPATH_DEFAULT + [('Prefix', None)],
        'tab_template': 'seeddb/tabs_prefix.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-prefix-edit', extra_context=extra)

def cabling_list(request):
    qs = Cabling.objects.all()
    value_list = ('room', 'jack', 'building', 'target_room', 'category', 'description')
    extra = {
        'title': TITLE_DEFAULT + ' - Cabling',
        'caption': 'Cabling',
        'navpath': NAVPATH_DEFAULT + [('Cabling', None)],
        'tab_template': 'seeddb/tabs_cabling.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-cabling-edit', extra_context=extra)

def patch_list(request):
    qs = Patch.objects.all()
    value_list = ('interface__netbox', 'interface__module', 'interface__baseport', 'cabling__room', 'cabling__jack', 'split')
    extra = {
        'title': TITLE_DEFAULT + ' - Patch',
        'caption': 'Patch',
        'navpath': NAVPATH_DEFAULT + [('Patch', None)],
        'tab_template': 'seeddb/tabs_patch.html',
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-patch-edit', extra_context=extra)

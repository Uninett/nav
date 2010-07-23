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
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404

from nav.django.utils import get_verbose_name
from nav.web.message import new_message, Messages
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.service import Service

from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.forms import RoomForm, LocationForm, OrganizationForm, \
    UsageForm, NetboxTypeForm, VendorForm, SubcategoryForm, PrefixForm, \
    CablingForm, PatchForm

NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def netbox_sysname(form):
    try:
        ip = IP(form.cleaned_data['name'])
    except ValueError:
        sysname = form.cleaned_data['name']
        ip = IP(gethostbyname(sysname))
    else:
        sysname = gethostbyaddr(unicode(ip))[0]
    return (ip, sysname)

def snmp_type(ip, ro, snmp_version):
    snmp = Snmp(unicode(ip), ro, snmp_version)
    try:
        sysobjectid = snmp.get('.1.3.6.1.2.1.1.2.0')
    except SnmpError:
        return None
    sysobjectid = sysobjectid.lstrip('.')
    try:
        type = NetboxType.objects.get(sysobjectid=sysobjectid)
        return type.id
    except NetboxType.DoesNotExist:
        return None 

def snmp_serials(ip, ro, snmp_version):
    snmp = Snmp(ip, ro, snmp_version)
    oids = SnmpOid.objects.filter(oid_key__icontains='serial').values('snmp_oid', 'get_next')
    serials = []
    for (oid, get_next) in oids:
        try:
            if get_next:
                result = snmp.walk(oid)
                serials.extend([r[1] for r in result if r[1]])
            else:
                result = snmp.get(oid)
                if result:
                    serials.append(result)
        except SnmpError:
            pass
    return serials

def netbox_edit(request, netbox_sysname=None):
    netbox = None
    if netbox_sysname:
        netbox = Netbox.objects.get(sysname=netbox_sysname)

    if request.method == 'POST':
        step = int(request.POST.get('step'))
        if step == 0:
            form = NetboxSysnameForm(request.POST)
            if form.is_valid():
                (ip, sysname) = netbox_sysname(form)
                if form.snmp_version:
                    ro = form.cleaned_data.get('read_only')
                    type = snmp_type(ip, ro, form.snmp_version)
                    serials = snmp_serials(ip, ro, form.snmp_version)
                    serial = None
                    if serials:
                        serial = serials[0]
                    raise Exception(serial)
    else:
        form = NetboxSysnameForm()

    context = {
        'object': netbox,
        'form': form,
        'active': {'add': True},
        'tab_template': 'seeddb/tabs_netbox.html',
    }
    return render_to_response('seeddb/edit.html',
        context, RequestContext(request))

def service_edit(request, service_id=None):
    # FIXME
    raise Exception, "Not implemented"

def room_edit(request, room_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
    }
    return render_edit(request, Room, RoomForm, room_id,
        'seeddb-room-edit',
        extra_context=extra)

def location_edit(request, location_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Location', reverse('seeddb-location'))],
        'tab_template': 'seeddb/tabs_location.html',
    }
    return render_edit(request, Location, LocationForm, location_id,
        'seeddb-location-edit',
        extra_context=extra)

def organization_edit(request, organization_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Organization', reverse('seeddb-organization'))],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_edit(request, Organization, OrganizationForm, organization_id, 
        'seeddb-organization-edit',
        extra_context=extra)

def usage_edit(request, usage_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Usage', reverse('seeddb-usage'))],
        'tab_template': 'seeddb/tabs_usage.html',
    }
    return render_edit(request, Usage, UsageForm, usage_id,
        'seeddb-usage-edit',
        extra_context=extra)

def netboxtype_edit(request, type_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Type', reverse('seeddb-type'))],
        'tab_template': 'seeddb/tabs_type.html',
    }
    return render_edit(request, NetboxType, NetboxTypeForm, type_id,
        'seeddb-type-edit',
        extra_context=extra)

def vendor_edit(request, vendor_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Vendor', reverse('seeddb-vendor'))],
        'tab_template': 'seeddb/tabs_vendor.html',
    }
    return render_edit(request, Vendor, VendorForm, vendor_id,
        'seeddb-vendor-edit',
        extra_context=extra)

def subcategory_edit(request, subcategory_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Subcategory', reverse('seeddb-subcategory'))],
        'tab_template': 'seeddb/tabs_subcategory.html',
    }
    return render_edit(request, Subcategory, SubcategoryForm, subcategory_id,
        'seeddb-subcategory-edit',
        extra_context=extra)

def vlan_edit(request, vlan_id=None):
    # FIXME
    raise Exception, "Not implemented"

def prefix_edit(request, prefix_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Prefix', reverse('seeddb-prefix'))],
        'tab_template': 'seeddb/tabs_prefix.html',
    }
    return render_edit(request, Prefix, PrefixForm, prefix_id,
        'seeddb-prefix-edit',
        extra_context=extra)

def cabling_edit(request, cabling_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Cabling', reverse('seeddb-cabling'))],
        'tab_template': 'seeddb/tabs_cabling.html',
    }
    return render_edit(request, Cabling, CablingForm, cabling_id,
        'seeddb-cabling-edit',
        extra_context=extra)

def patch_edit(request, patch_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Patch', reverse('seeddb-patch'))],
        'tab_template': 'seeddb/tabs_patch.html',
    }
    return render_edit(request, Patch, PatchForm, patch_id,
        'seeddb-patch-edit',
        extra_context=extra)

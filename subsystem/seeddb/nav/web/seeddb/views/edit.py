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

from IPy import IP
from socket import gethostbyaddr, gethostbyname

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404

from nav.django.utils import get_verbose_name
from nav.web.message import new_message, Messages
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization, Device
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.service import Service
from nav.models.oid import SnmpOid
from nav.Snmp import Snmp, SnmpError

from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.forms import RoomForm, LocationForm, OrganizationForm, \
    UsageForm, NetboxTypeForm, VendorForm, SubcategoryForm, PrefixForm, \
    CablingForm, PatchForm, NetboxStep1, NetboxStep2, NetboxStep3

NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def ip_and_sysname(form):
    try:
        ip = IP(form.cleaned_data['name'])
    except ValueError:
        sysname = form.cleaned_data['name']
        ip = IP(gethostbyname(sysname))
    else:
        sysname = gethostbyaddr(unicode(ip))[0]
    return (ip, sysname)

def snmp_type(ip, ro, snmp_version):
    snmp = Snmp(ip, ro, snmp_version)
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
    oids = SnmpOid.objects.filter(oid_key__icontains='serial').values_list('snmp_oid', 'get_next')
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
    form_data = {}
    hidden_form = None

    if netbox_sysname:
        netbox = Netbox.objects.get(sysname=netbox_sysname)
    try:
        step = int(request.POST.get('step', '0'))
    except ValueError:
        step = 0

    if request.method == 'POST':
        if step == 1:
            form = NetboxStep1(request.POST)
            if form.is_valid():
                ip = form.ip
                sysname = form.sysname
                form_data = {
                    'ip': unicode(ip),
                    'sysname': sysname,
                }
                form = NetboxStep2(initial=form_data)
                step = 2
        elif step == 2:
            form = NetboxStep2(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                serial = None
                type = None
                if form.snmp_version:
                    ip = data.get('ip')
                    ro = data.get('read_only')
                    type = snmp_type(ip, ro, form.snmp_version)
                    serials = snmp_serials(ip, ro, form.snmp_version)
                    serial = None
                    if serials:
                        serial = serials[0]
                form_data = data
                form_data['room'] = data['room'].pk
                form_data['category'] = data['category'].pk
                form_data['organization'] = data['organization'].pk
                form_data['serial'] = serial
                form_data['type'] = type
                form_data['snmp_version'] = form.snmp_version
                if len(form_data['snmp_version']) > 1:
                    form_data['snmp_version'] = form_data['snmp_version'][0]
                form = NetboxStep3(initial=form_data)
                if serial and type:
                    form.is_valid()
                step = 3
        elif step == 3:
            form = NetboxStep3(request.POST)
            if form.is_valid():
                form_data = form.cleaned_data
                device, created = Device.objects.get_or_create(serial=form_data['serial'])
                netbox = form.save(commit=False)
                netbox.device = device
                netbox.save()
                form.save_m2m()
                new_message(request._req, "Hello", Messages.SUCCESS)
    else:
        form = NetboxStep1()
        step = 1

    context = {
        'step': step,
        'data': form_data,
        'object': netbox,
        'form': form,
        'hidden_form': hidden_form,
        'sub_active': {'add': True},
        'tab_template': 'seeddb/tabs_netbox.html',
    }
    return render_to_response('seeddb/netbox_wizard.html',
        context, RequestContext(request))

def service_edit(request, service_id=None):
    # FIXME
    raise Exception, "Not implemented"

def room_edit(request, room_id=None):
    extra = {
        'active': {'room': True},
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
    }
    return render_edit(request, Room, RoomForm, room_id,
        'seeddb-room-edit',
        extra_context=extra)

def location_edit(request, location_id=None):
    extra = {
        'active': {'location': True},
        'navpath': NAVPATH_DEFAULT + [('Location', reverse('seeddb-location'))],
        'tab_template': 'seeddb/tabs_location.html',
    }
    return render_edit(request, Location, LocationForm, location_id,
        'seeddb-location-edit',
        extra_context=extra)

def organization_edit(request, organization_id=None):
    extra = {
        'active': {'organization': True},
        'navpath': NAVPATH_DEFAULT + [('Organization', reverse('seeddb-organization'))],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_edit(request, Organization, OrganizationForm, organization_id, 
        'seeddb-organization-edit',
        extra_context=extra)

def usage_edit(request, usage_id=None):
    extra = {
        'active': {'usage': True},
        'navpath': NAVPATH_DEFAULT + [('Usage', reverse('seeddb-usage'))],
        'tab_template': 'seeddb/tabs_usage.html',
    }
    return render_edit(request, Usage, UsageForm, usage_id,
        'seeddb-usage-edit',
        extra_context=extra)

def netboxtype_edit(request, type_id=None):
    extra = {
        'active': {'type': True},
        'navpath': NAVPATH_DEFAULT + [('Type', reverse('seeddb-type'))],
        'tab_template': 'seeddb/tabs_type.html',
    }
    return render_edit(request, NetboxType, NetboxTypeForm, type_id,
        'seeddb-type-edit',
        extra_context=extra)

def vendor_edit(request, vendor_id=None):
    extra = {
        'active': {'vendor': True},
        'navpath': NAVPATH_DEFAULT + [('Vendor', reverse('seeddb-vendor'))],
        'tab_template': 'seeddb/tabs_vendor.html',
    }
    return render_edit(request, Vendor, VendorForm, vendor_id,
        'seeddb-vendor-edit',
        extra_context=extra)

def subcategory_edit(request, subcategory_id=None):
    extra = {
        'active': {'subcategory': True},
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
        'active': {'prefix': True},
        'navpath': NAVPATH_DEFAULT + [('Prefix', reverse('seeddb-prefix'))],
        'tab_template': 'seeddb/tabs_prefix.html',
    }
    return render_edit(request, Prefix, PrefixForm, prefix_id,
        'seeddb-prefix-edit',
        extra_context=extra)

def cabling_edit(request, cabling_id=None):
    extra = {
        'active': {'cabling': True},
        'navpath': NAVPATH_DEFAULT + [('Cabling', reverse('seeddb-cabling'))],
        'tab_template': 'seeddb/tabs_cabling.html',
    }
    return render_edit(request, Cabling, CablingForm, cabling_id,
        'seeddb-cabling-edit',
        extra_context=extra)

def patch_edit(request, patch_id=None):
    extra = {
        'active': {'patch': True},
        'navpath': NAVPATH_DEFAULT + [('Patch', reverse('seeddb-patch'))],
        'tab_template': 'seeddb/tabs_patch.html',
    }
    return render_edit(request, Patch, PatchForm, patch_id,
        'seeddb-patch-edit',
        extra_context=extra)

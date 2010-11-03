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
from django.db import transaction
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404

from nav.django.utils import get_verbose_name
from nav.web.message import new_message, Messages
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization, Device
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix, NetboxCategory
from nav.models.service import Service
from nav.models.oid import SnmpOid
from nav.Snmp import Snmp, SnmpError

from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.forms import RoomForm, LocationForm, OrganizationForm, \
    UsageForm, NetboxTypeForm, VendorForm, SubcategoryForm, PrefixForm, \
    CablingForm, PatchForm, NetboxForm, NetboxSerialForm, NetboxSubcategoryForm, get_netbox_subcategory_form, NetboxReadonlyForm

NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

def snmp_type(ip, ro, snmp_version):
    snmp = Snmp(ip, ro, snmp_version)
    try:
        sysobjectid = snmp.get('.1.3.6.1.2.1.1.2.0')
    except SnmpError:
        return None
    sysobjectid = sysobjectid.lstrip('.')
    try:
        netbox_type = NetboxType.objects.get(sysobjectid=sysobjectid)
        return netbox_type
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
    FORM_STEP = 0
    SERIAL_STEP = 1
    SAVE_STEP = 2
    netbox = None
    form = None
    serial_form = None
    subcat_form = None

    if netbox_sysname:
        netbox = Netbox.objects.get(sysname=netbox_sysname)
    try:
        step = int(request.POST.get('step', '0'))
    except ValueError:
        step = FORM_STEP

    if request.method == 'POST':
        if step == SERIAL_STEP:
            form = NetboxForm(request.POST)
            if form.is_valid():
                serial, netbox_type = netbox_get_serial_and_type(form)
                form, serial_form, subcat_form = netbox_serial_and_subcat_form(
                    request, form, serial, netbox_type)
                step = SAVE_STEP
        elif step == SAVE_STEP:
            form = NetboxReadonlyForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                serial_form = NetboxSerialForm(request.POST, netbox_id=data['id'])
                subcat_form = get_netbox_subcategory_form(data['category'], post_data=request.POST)
                if serial_form.is_valid() and (not subcat_form or subcat_form.is_valid()):
                    return netbox_save(request, form, serial_form, subcat_form)
    else:
        if netbox:
            form_data = {
                'id': netbox.pk,
                'ip': netbox.ip,
                'room': netbox.room_id,
                'category': netbox.category_id,
                'organization': netbox.organization_id,
                'read_only': netbox.read_only,
                'read_write': netbox.read_write,
            }
            form = NetboxForm(initial=form_data)
        else:
            form = NetboxForm()
        step = SERIAL_STEP

    context = {
        'step': step,
        'object': netbox,
        'form': form,
        'serial_form': serial_form,
        'subcat_form': subcat_form,
        'sub_active': {'add': True},
        'tab_template': 'seeddb/tabs_netbox.html',
    }
    return render_to_response('seeddb/netbox_wizard.html',
        context, RequestContext(request))

def netbox_get_serial_and_type(form):
    data = form.cleaned_data
    serial = None
    netbox_type = None
    ro = data.get('read_only')
    if ro:
        ip = data.get('ip')
        netbox_type = snmp_type(ip, ro, form.snmp_version)
        serials = snmp_serials(ip, ro, form.snmp_version)
        serial = None
        if serials:
            serial = serials[0]
    return (serial, netbox_type)

def netbox_serial_and_subcat_form(request, form, serial, netbox_type):
    data = form.cleaned_data
    form_data = data
    form_data['room'] = data['room'].pk
    form_data['category'] = data['category'].pk
    form_data['organization'] = data['organization'].pk
    form_data['serial'] = serial
    form_data['snmp_version'] = form.snmp_version
    form_data['sysname'] = form.sysname
    if len(form_data['snmp_version']) > 1:
        form_data['snmp_version'] = form_data['snmp_version'][0]
    if netbox_type:
        form_data['netbox_type'] = netbox_type.description
        form_data['type'] = netbox_type.pk

    serial_form = NetboxSerialForm(initial={'serial': serial}, netbox_id=data.get('id'))
    if serial:
        serial_form.is_valid()
    subcat_form = get_netbox_subcategory_form(data['category'], netbox_id=data.get('id'))
    form = NetboxReadonlyForm(initial=form_data)

    return (form, serial_form, subcat_form)

@transaction.commit_on_success
def netbox_save(request, form, serial_form, subcat_form):
    clean_data = form.cleaned_data
    primary_key = clean_data.get('id')
    data = {
        'ip': clean_data['ip'],
        'sysname': clean_data['sysname'],
        'room': clean_data['room'],
        'category': clean_data['category'],
        'organization': clean_data['organization'],
        'read_only': clean_data['read_only'],
        'read_write': clean_data['read_write'],
        'snmp_version': clean_data['snmp_version'],
    }

    serial = serial_form.cleaned_data['serial']
    if serial:
        device, created = Device.objects.get_or_create(serial=serial)
        data['device'] = device
    elif not primary_key:
        device = Device.objects.create(serial=None)
        data['device'] = device

    if 'type' in clean_data and clean_data['type']:
        data['type'] = NetboxType.objects.get(pk=clean_data['type'])


    if primary_key:
        netbox = Netbox.objects.get(pk=primary_key)
        for key in data:
            netbox.__setattr__(key, data[key])
    else:
        netbox = Netbox(**data)

    netbox.save()

    if subcat_form:
        subcategories = subcat_form.cleaned_data['subcategories']
        NetboxCategory.objects.filter(netbox=netbox).delete()
        for subcat in subcategories:
            NetboxCategory.objects.create(netbox=netbox, category=subcat)

    new_message(request._req,
        "Saved netbox %s" % netbox.sysname,
        Messages.SUCCESS)
    return HttpResponseRedirect(reverse('seeddb-netbox'))

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

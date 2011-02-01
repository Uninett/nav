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
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.web.message import new_message, Messages
from nav.web.quickselect import QuickSelect
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization
from nav.models.manage import Usage, Vendor, Subcategory, Prefix, Vlan
from nav.models.service import Service, ServiceProperty
from nav.web.serviceHelper import getDescription

from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.netbox_edit import netbox_get_serial_and_type
from nav.web.seeddb.utils.netbox_edit import netbox_serial_and_subcat_form
from nav.web.seeddb.utils.netbox_edit import netbox_save
from nav.web.seeddb.utils.service_edit import service_save
from nav.web.seeddb.forms import get_netbox_subcategory_form, NetboxReadonlyForm
from nav.web.seeddb.forms import RoomForm, LocationForm, OrganizationForm
from nav.web.seeddb.forms import UsageForm, NetboxTypeForm, VendorForm
from nav.web.seeddb.forms import SubcategoryForm, PrefixForm, CablingForm
from nav.web.seeddb.forms import PatchForm, NetboxForm, NetboxSerialForm
from nav.web.seeddb.forms import ServiceForm, ServicePropertyForm
from nav.web.seeddb.forms import VlanForm, ServiceChoiceForm

NAVPATH_DEFAULT = [('Home', '/'), ('Seed DB', '/seeddb/')]

FORM_STEP = 0
SERIAL_STEP = 1
SAVE_STEP = 2

def netbox_edit(request, netbox_id=None):
    netbox = None
    form = None
    serial_form = None
    subcat_form = None

    if netbox_id:
        netbox = Netbox.objects.get(id=netbox_id)
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
                    form, serial, netbox_type)
                step = SAVE_STEP
        elif step == SAVE_STEP:
            form = NetboxReadonlyForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                serial_form = NetboxSerialForm(
                    request.POST, netbox_id=data['id'])
                subcat_form = get_netbox_subcategory_form(
                    data['category'], post_data=request.POST)

                subcat_form_valid = not subcat_form or subcat_form.is_valid()
                if serial_form.is_valid() and subcat_form_valid:
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
        'sub_active': netbox and {'edit': True} or {'add': True},
        'tab_template': 'seeddb/tabs_netbox.html',
    }
    return render_to_response('seeddb/netbox_wizard.html',
        context, RequestContext(request))

def service_edit(request, service_id=None):
    service = None
    netbox = None
    service_form = None
    property_form = None
    if service_id:
        service = Service.objects.get(pk=service_id)

    if request.method == 'POST' and 'save' in request.POST:
        service_form = ServiceForm(request.POST)
        if service_form.is_valid():
            handler = service_form.cleaned_data['handler']
            property_form = ServicePropertyForm(request.POST,
                service_args=getDescription(handler))
            if property_form.is_valid():
                return service_save(request, service_form, property_form)
    else:
        if not service_id:
            return service_add(request)
        else:
            handler = service.handler
            netbox = service.netbox
            service_prop = ServiceProperty.objects.filter(service=service)
            service_form = ServiceForm(initial={
                'service': service.pk,
                'netbox': netbox.pk,
                'handler': handler,
            })
            initial = dict(
                [(prop.property, prop.value) for prop in service_prop])
            property_form = ServicePropertyForm(
                service_args=getDescription(service.handler),
                initial=initial)

    context = {
        'object': service,
        'handler': handler,
        'netbox': netbox,
        'active': {'service': True},
        'sub_active': {'edit': True},
        'service_form': service_form,
        'property_form': property_form,
        'navpath': NAVPATH_DEFAULT + [('Service', reverse('seeddb-service'))],
        'tab_template': 'seeddb/tabs_service.html',
        'title': 'NAV - Seed Database - Add service',
    }
    return render_to_response('seeddb/service_property_form.html',
        context, RequestContext(request))

def service_add(request):
    box_select = QuickSelect(
        location=False,
        room=False,
        netbox=True,
        netbox_multiple=False)
    if request.method == 'POST':
        choice_form = ServiceChoiceForm(request.POST)
        netbox_id = request.POST.get('netbox')
        try:
            netbox = Netbox.objects.get(pk=netbox_id)
        except Netbox.DoesNotExist:
            new_message(
                request._req,
                "Netbox does not exist in database",
                Messages.ERROR)
        else:
            if choice_form.is_valid():
                property_form = ServicePropertyForm(
                    service_args=getDescription(
                        choice_form.cleaned_data['service']
                    ))
                service_form = ServiceForm(initial={
                    'netbox': netbox.pk,
                    'handler': choice_form.cleaned_data['service'],
                })
                context = {
                    'service_form': service_form,
                    'property_form': property_form,
                    'active': {'service': True},
                    'sub_active': {'add': True},
                    'navpath': NAVPATH_DEFAULT + [
                        ('Service', reverse('seeddb-service'))
                    ],
                    'tab_template': 'seeddb/tabs_service.html',
                    'title': 'NAV - Seed Database - Add service',
                    'handler': choice_form.cleaned_data['service'],
                    'netbox': netbox,
                }
                return render_to_response('seeddb/service_property_form.html',
                    context, RequestContext(request))
    else:
        choice_form = ServiceChoiceForm()

    context = {
        'box_select': box_select,
        'choice_form': choice_form,
        'active': {'service': True},
        'sub_active': {'add': True},
        'navpath': NAVPATH_DEFAULT + [('Service', reverse('seeddb-service'))],
        'tab_template': 'seeddb/tabs_service.html',
        'title': 'NAV - Seed Database - Add service',
    }
    return render_to_response('seeddb/service_netbox_form.html',
        context, RequestContext(request))

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
        'navpath': NAVPATH_DEFAULT + [
            ('Organization', reverse('seeddb-organization'))
        ],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_edit(request, Organization, OrganizationForm,
        organization_id, 'seeddb-organization-edit',
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
        'navpath': NAVPATH_DEFAULT + [
            ('Subcategory', reverse('seeddb-subcategory'))
        ],
        'tab_template': 'seeddb/tabs_subcategory.html',
    }
    return render_edit(request, Subcategory, SubcategoryForm, subcategory_id,
        'seeddb-subcategory-edit',
        extra_context=extra)

def vlan_edit(request, vlan_id=None):
    extra = {
        'active': {'vlan': True},
        'navpath': NAVPATH_DEFAULT + [('Vlan', reverse('seeddb-vlan'))],
        'tab_template': 'seeddb/tabs_vlan.html',
    }
    return render_edit(request, Vlan, VlanForm, vlan_id,
        'seeddb-vlan-edit',
        extra_context=extra)

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

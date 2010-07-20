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
from socket import gethostbyname, gethostbyaddr

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
from nav.Snmp import Snmp

from nav.web.seeddb.forms import *
from nav.web.seeddb.utils import *
from nav.web.seeddb.views.list import NetboxList

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

def netbox_list(request):
    if request.method == 'POST':
        if 'move' in request.POST:
            return netbox_move(request)
        elif 'delete' in request.POST:
            pass
    return NetboxList(request)

def netbox_move(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('seeddb-netbox'))
    return move(request, Netbox, NetboxMoveForm, 'seeddb-netbox', title_attr='sysname')

def room_edit(request, room_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Rooms', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
    }
    return render_seeddb_edit(request, Room, RoomForm,
        room_id, extra_context=extra)

def room_move(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('seeddb-room'))
    return move(request, Room, RoomMoveForm)

def room_delete(request):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('seeddb-room'))

    rooms = Room.objects.order_by('id').filter(id__in=request.POST.getlist('object'))
    if request.POST.get('confirm'):
        rooms.delete()
        new_message(request._req, "Deleted", Messages.SUCCESS)
        return HttpResponseRedirect(reverse('seeddb-room'))

    cabling_qs = Cabling.objects.filter(room__in=rooms).values('id', 'room')
    netbox_qs = Netbox.objects.filter(room__in=rooms).values('id', 'room', 'sysname')
    cabling = group_query(cabling_qs, 'room')
    netbox = group_query(netbox_qs, 'room')

    objects = []
    errors = False
    for r in rooms:
        object = {
            'object': r,
            'disabled': False,
            'error': [],
        }
        for n in netbox.get(r.id, []):
            errors = True
            object['disabled'] = True
            object['error'].append({
                'message': "Used in netbox",
                'title': n['sysname'],
                'url': reverse('seeddb-netbox-edit', args=(n['id'],)),
            })
        if r.id in cabling and len(cabling[r.id]) > 0:
            object['error'].append("Used in cabling")
            errors = True
        objects.append(object)

    context = {
        'objects': objects,
        'errors': errors,
    }
    return render_to_response('seeddb/delete.html',
        context, RequestContext(request))

def location_edit(request, location_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Locations', None)],
        'tab_template': 'seeddb/tabs_location.html',
    }
    return render_seeddb_edit(request, Location, LocationForm,
        location_id, extra_context=extra)

def organization_edit(request, organization_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Organizations', reverse('seeddb-organization'))],
        'tab_template': 'seeddb/tabs_organization.html',
    }
    return render_seeddb_edit(request, Organization, OrganizationForm,
        organization_id, extra_context=extra)

def usage_edit(request, usage_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Usage categories', reverse('seeddb-usage'))],
        'tab_template': 'seeddb/tabs_usage.html',
    }
    return render_seeddb_edit(request, Usage, UsageForm,
        usage_id, extra_context=extra)

def type_edit(request, type_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Types', reverse('seeddb-type'))],
        'tab_template': 'seeddb/tabs_type.html',
    }
    return render_seeddb_edit(request, NetboxType, NetboxTypeForm,
        type_id, title_attr='name', extra_context=extra)

def vendor_edit(request, vendor_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Vendors', reverse('seeddb-vendor'))],
        'tab_template': 'seeddb/tabs_vendor.html',
    }
    return render_seeddb_edit(request, Vendor, VendorForm,
        vendor_id, extra_context=extra)

def subcategory_edit(request, subcategory_id=None):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Subcategories', reverse('seeddb-subcategory'))],
        'tab_template': 'seeddb/tabs_subcategory.html',
    }
    return render_seeddb_edit(request, Subcategory, SubcategoryForm,
        subcategory_id, extra_context=extra)

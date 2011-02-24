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
from django.http import HttpResponseRedirect
from django.db import transaction

from nav.models.oid import SnmpOid
from nav.Snmp import Snmp, SnmpError
from nav.models.manage import Device, NetboxType, NetboxCategory, Netbox
from nav.web.message import new_message, Messages

from nav.web.seeddb.forms import get_netbox_subcategory_form, NetboxReadonlyForm
from nav.web.seeddb.forms import NetboxSerialForm

def snmp_type(ip_addr, snmp_ro, snmp_version):
    snmp = Snmp(ip_addr, snmp_ro, snmp_version)
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

def snmp_serials(ip_addr, snmp_ro, snmp_version):
    snmp = Snmp(ip_addr, snmp_ro, snmp_version)
    oids = SnmpOid.objects.filter(
        oid_key__icontains='serial'
    ).values_list(
        'snmp_oid', 'get_next'
    )
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

def netbox_get_serial_and_type(form):
    data = form.cleaned_data
    serial = None
    netbox_type = None
    snmp_ro = data.get('read_only')
    if snmp_ro:
        ip_addr = data.get('ip')
        netbox_type = snmp_type(ip_addr, snmp_ro, form.snmp_version)
        serials = snmp_serials(ip_addr, snmp_ro, form.snmp_version)
        serial = None
        if serials:
            serial = serials[0]
    return (serial, netbox_type)

def netbox_serial_and_subcat_form(form, serial, netbox_type):
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

    serial_form = NetboxSerialForm(
        initial={'serial': serial},
        netbox_id=data.get('id'))
    if serial:
        serial_form.is_valid()
    subcat_form = get_netbox_subcategory_form(
        data['category'],
        netbox_id=data.get('id'))
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
            setattr(netbox, key, data[key])
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

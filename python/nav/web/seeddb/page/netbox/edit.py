#
# Copyright (C) 2011, 2012 UNINETT AS
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

"""Controls add and edit of ip devices"""

# pylint: disable=F0401

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db import transaction

from nav.models.manage import Netbox, Device, NetboxCategory, NetboxType
from nav.models.manage import NetboxInfo
from nav.models.oid import SnmpOid
from nav.Snmp import Snmp
from nav.Snmp.errors import SnmpError
from nav.web.message import new_message, Messages

from nav.web.seeddb import reverse_lazy
from nav.web.seeddb.page.netbox import NetboxInfo as NI
from nav.web.seeddb.page.netbox.forms import NetboxForm, NetboxReadonlyForm
from nav.web.seeddb.page.netbox.forms import NetboxSerialForm
from nav.web.seeddb.page.netbox.forms import get_netbox_group_form

FORM_STEP = 0
SERIAL_STEP = 1
SAVE_STEP = 2


def netbox_edit(request, netbox_id=None):
    """Controller for edit or create of netbox"""
    try:
        step = int(request.POST.get('step', '0'))
    except ValueError:
        step = FORM_STEP

    serial_form = None
    group_form = None
    netbox = get_netbox(netbox_id)
    title = get_title(netbox)
    if request.method == 'POST':
        if step == SERIAL_STEP:
            netbox_form = NetboxForm(request.POST)
            if netbox_form.is_valid():
                netbox_form, serial_form, group_form = netbox_serial_and_type(
                    netbox_form, netbox_id)
                step = SAVE_STEP
        else:
            (forms_are_valid,
             netbox_form,
             serial_form,
             group_form) = netbox_validate_before_save(request)

            if forms_are_valid:
                netbox = netbox_do_save(netbox_form, serial_form, group_form)
                new_message(request, "Saved netbox %s" % netbox.sysname,
                            Messages.SUCCESS)
                return HttpResponseRedirect(reverse('seeddb-netbox'))
    else:
        netbox_form = get_netbox_form(netbox)
        step = SERIAL_STEP
    return netbox_render(request, step, netbox, netbox_form, serial_form,
                         group_form, title)


def get_netbox(netbox_id):
    """Get netbox with id or return None if none is found"""
    try:
        return Netbox.objects.get(id=netbox_id)
    except Netbox.DoesNotExist:
        return None


def get_title(netbox):
    """Return correct title based on if netbox exists or not"""
    return "Edit IP Device" if netbox else "Add new IP Device"


def get_netbox_form(netbox):
    """Get form object for netbox or create if no netbox"""
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
    return form


def netbox_serial_and_type(form, netbox_id):
    """If netbox form is valid, create and return serial and group form"""
    ro_form = serial_form = group_form = None
    if form.is_valid():
        serial, netbox_type = netbox_get_serial_and_type(form)
        function = netbox_get_function(netbox_id)
        ro_form, serial_form, group_form = netbox_serial_and_group_form(
            form, serial, function, netbox_type)
    return ro_form, serial_form, group_form


def netbox_validate_before_save(request):
    """Validate netbox before save"""
    form = NetboxReadonlyForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        serial_form = NetboxSerialForm(
            request.POST, netbox_id=data['id'])
        group_form = get_netbox_group_form(post_data=request.POST)

        serial_form_valid = serial_form and serial_form.is_valid()
        group_form_valid = not group_form or group_form.is_valid()

        return (serial_form_valid and group_form_valid,
                form, serial_form, group_form)
    else:
        return False, form, None, None


def netbox_render(request, step, netbox, netbox_form, serial_form, group_form,
                  title):
    """Move some code to another function to make it cleaner"""
    info = NI()
    context = info.template_context
    context.update({
        'step': step,
        'object': netbox,
        'form': netbox_form,
        'serial_form': serial_form,
        'netboxgroup_form': group_form,
        'title': title,
        '_navpath': [('Edit Device', reverse_lazy('seeddb-netbox-edit'))],
        'sub_active': netbox and {'edit': True} or {'add': True},
        'tab_template': 'seeddb/tabs_generic.html',
    })
    return render_to_response('seeddb/netbox_wizard.html', context,
                              RequestContext(request))


def snmp_type(ip_addr, snmp_ro, snmp_version):
    """Query ip for sysobjectid using form data"""
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
    """Query ip for serial using form data"""
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
    """Use form data to query for serial and sysobjectid"""
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


def netbox_get_function(netbox_id):
    """Check if we have a function set for this netbox id"""
    func = None
    if netbox_id:
        try:
            func = NetboxInfo.objects.get(
                netbox=netbox_id, variable='function'
            ).value
        except NetboxInfo.DoesNotExist:
            pass
    return func


def netbox_serial_and_group_form(form, serial, function, netbox_type):
    """Create serial and netboxgroup form based on first form"""
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

    serial_form_initial = {
        'serial': serial,
        'function': function,
    }
    serial_form = NetboxSerialForm(
        initial=serial_form_initial,
        netbox_id=data.get('id'))
    if serial:
        serial_form.is_valid()
    netbox_group_form = get_netbox_group_form(netbox_id=data.get('id'))
    ro_form = NetboxReadonlyForm(initial=form_data)

    return ro_form, serial_form, netbox_group_form

@transaction.commit_on_success
def netbox_do_save(form, serial_form, group_form):
    """Save netbox"""
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
        'up_to_date': False,
    }

    serial = serial_form.cleaned_data['serial']
    if serial:
        device, _ = Device.objects.get_or_create(serial=serial)
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

    function = serial_form.cleaned_data['function']
    if function:
        try:
            func = NetboxInfo.objects.get(netbox=netbox, variable='function')
        except NetboxInfo.DoesNotExist:
            func = NetboxInfo(
                netbox=netbox, variable='function', value=function
            )
        else:
            func.value = function
        func.save()

    if group_form:
        netboxgroups = group_form.cleaned_data['netboxgroups']
        NetboxCategory.objects.filter(netbox=netbox).delete()
        for netboxgroup in netboxgroups:
            NetboxCategory.objects.create(netbox=netbox, category=netboxgroup)

    return netbox

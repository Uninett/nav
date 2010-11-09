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

from socket import error as SocketError

from django import forms
from django.db.models import Q

from nav.Snmp import Snmp, TimeOutException, SnmpError
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.manage import Category, Device, NetboxCategory
from nav.models.service import Service, ServiceProperty
from nav.web.serviceHelper import getCheckers

from nav.web.seeddb.utils.edit import resolve_ip_and_sysname, does_ip_exist
from nav.web.seeddb.utils.edit import does_sysname_exist

READONLY_WIDGET_ATTRS = {
    'readonly': 'readonly',
    'class': 'readonly',
}

class NetboxForm(forms.Form):
    id = forms.IntegerField(
        required=False, widget=forms.HiddenInput)
    ip = forms.CharField()
    room = forms.ModelChoiceField(queryset=Room.objects.all())
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    organization = forms.ModelChoiceField(queryset=Organization.objects.all())
    read_only = forms.CharField(required=False)
    read_write = forms.CharField(required=False)

    def clean_ip(self):
        name = self.cleaned_data['ip']
        try:
            ip, sysname = resolve_ip_and_sysname(name)
        except SocketError:
            raise forms.ValidationError("Could not resolve name %s" % name)
        self.sysname = sysname
        return unicode(ip)

    def clean(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('id')
        ip = cleaned_data.get('ip')
        cat = cleaned_data.get('category')
        ro = cleaned_data.get('read_only')
        self.snmp_version = '1'

        if ip:
            msg = []
            if does_ip_exist(ip, id):
                msg.append("IP (%s) is already in database" % ip)
            if does_sysname_exist(self.sysname, id):
                msg.append("Sysname (%s) is already in database" % self.sysname)
            if len(msg) > 0:
                self._errors['ip'] = self.error_class(msg)
                del cleaned_data['ip']

        if cat and cat.req_snmp and not ro:
            self._errors['read_only'] = self.error_class(["Category %s requires SNMP access." % cat.id])
            del cleaned_data['category']
            del cleaned_data['read_only']

        if ro and ip:
            sysobjectid = '1.3.6.1.2.1.1.2.0'
            try:
                try:
                    snmp = Snmp(ip, ro, '2c')
                    typeid = snmp.get(sysobjectid)
                    self.snmp_version = '2c'
                except TimeOutException:
                    snmp = Snmp(ip, ro, '1')
                    typeid = snmp.get(sysobjectid)
                    self.snmp_version = '1'
            except SnmpError:
                if cat and cat.req_snmp:
                    msg = (
                        "No SNMP response.",
                        "Is read only community correct?")
                else:
                    msg = (
                        "No SNMP response.",
                        "SNMP is not required for this category, if you don't need SNMP please leave the 'Read only' field empty.")
                self._errors['read_only'] = self.error_class(msg)
                del cleaned_data['read_only']

        return cleaned_data

class NetboxReadonlyForm(NetboxForm):
    sysname = forms.CharField()
    netbox_type = forms.CharField(required=False)
    type = forms.IntegerField(required=False,
        widget=forms.HiddenInput)
    snmp_version = forms.IntegerField(
        widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(NetboxReadonlyForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field in ('id', 'type'):
                continue
            self.fields[field].widget = forms.TextInput(attrs=READONLY_WIDGET_ATTRS)

class NetboxSerialForm(forms.Form):
    serial = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.netbox_id = kwargs.pop('netbox_id', None)
        super(NetboxSerialForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial')
        if initial and initial.get('serial'):
            self.fields['serial'].widget = forms.TextInput(attrs=READONLY_WIDGET_ATTRS)

    def clean_serial(self):
        serial = self.cleaned_data['serial']
        try:
            if self.netbox_id:
                netbox = Netbox.objects.get(
                    Q(device__serial=serial),
                    ~Q(id=self.netbox_id))
            else:
                netbox = Netbox.objects.get(device__serial=serial)
        except Netbox.DoesNotExist:
            return serial
        else:
            raise forms.ValidationError("Serial (%s) exists in database" % serial)

def get_netbox_subcategory_form(category, netbox_id=None, post_data=None):
    subcat = Subcategory.objects.filter(category=category).order_by('id')
    if subcat.count() > 0:
        if netbox_id and not post_data:
            subcats = NetboxCategory.objects.filter(netbox=netbox_id).values_list('category', flat=True)
            initial = {'subcategories': subcats}
            return NetboxSubcategoryForm(queryset=subcat, initial=initial)
        elif post_data:
            return NetboxSubcategoryForm(post_data, queryset=subcat)
        else:
            return NetboxSubcategoryForm(queryset=subcat)
    else:
        return None

class NetboxSubcategoryForm(forms.Form):
    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop('queryset')
        super(NetboxSubcategoryForm, self).__init__(*args, **kwargs)
        self.fields['subcategories'] = forms.ModelMultipleChoiceField(queryset=queryset, required=False)

class ServiceChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ServiceChoiceForm, self).__init__(*args, **kwargs)
        self.fields['service'] = forms.ChoiceField(
            choices=[(service, service) for service in getCheckers()])

class ServiceForm(forms.Form):
    service = forms.IntegerField(
        widget=forms.HiddenInput, required=False)
    handler = forms.CharField(
        widget=forms.HiddenInput)
    netbox = forms.IntegerField(
        widget=forms.HiddenInput)

class ServicePropertyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        service_description = kwargs.pop('service_args')
        super(ServicePropertyForm, self).__init__(*args, **kwargs)
        args = service_description.get('args')
        opt_args = service_description.get('optargs')

        if args:
            for arg in args:
                self.fields[arg] = forms.CharField(required=True)
        if opt_args:
            for arg in opt_args:
                self.fields[arg] = forms.CharField(required=False)

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            del self.fields['id']

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            del self.fields['id']

class UsageForm(forms.ModelForm):
    class Meta:
        model = Usage

    def __init__(self, *args, **kwargs):
        super(UsageForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            del self.fields['id']

class NetboxTypeForm(forms.ModelForm):
    class Meta:
        model = NetboxType

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor

class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory

class VlanForm(forms.ModelForm):
    class Meta:
        model = Vlan

class PrefixForm(forms.ModelForm):
    class Meta:
        model = Prefix

class CablingForm(forms.ModelForm):
    class Meta:
        model = Cabling

class PatchForm(forms.ModelForm):
    class Meta:
        model = Patch

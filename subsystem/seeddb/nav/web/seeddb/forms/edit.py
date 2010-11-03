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
from socket import gethostbyaddr, gethostbyname, error as SocketError

from django import forms

from nav.Snmp import Snmp, TimeOutException, SnmpError
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization
from nav.models.manage import Usage, Vendor, Subcategory, Vlan, Prefix
from nav.models.manage import Category, Device
from nav.models.service import Service

from nav.web.seeddb.utils.edit import resolve_ip_and_sysname, does_ip_exist
from nav.web.seeddb.utils.edit import does_sysname_exist

READONLY_WIDGET_ATTRS = {
    'readonly': 'readonly',
    'class': 'readonly',
}

class NetboxStep1(forms.Form):
    name = forms.CharField(label=u"Sysname or IP")

    def clean(self):
        data = self.cleaned_data
        name = data.get('name')
        if name:
            try:
                self.ip, self.sysname = resolve_ip_and_sysname(name)
            except SocketError:
                msg = ("Could not resolve name %s" % name,)
                self._errors['name'] = self.error_class(msg)
                del data['name']
            else:
                msg = []
                if does_ip_exist(self.ip):
                    msg.append("IP (%s) is already in database" % self.ip)
                if does_sysname_exist(self.sysname):
                    msg.append("Sysname (%s) is already in database" % self.sysname)
                if len(msg) > 0:
                    self._errors['name'] = self.error_class(msg)
                    del data['name']
        return data

class NetboxStep2(forms.ModelForm):
    class Meta:
        model = Netbox
        fields = ('ip', 'sysname', 'category', 'read_only', 'read_write',
        'room', 'organization')

    def __init__(self, data=None, *args, **kwargs):
        super(NetboxStep2, self).__init__(data, *args, **kwargs)
        self.fields['sysname'].widget = forms.TextInput(attrs=READONLY_WIDGET_ATTRS)
        if 'initial' in kwargs or data:
            initial = kwargs.get('initial', {})
            data = data or {}
            if 'ip' in initial or 'ip' in data:
                self.fields['ip'].widget = forms.TextInput(attrs=READONLY_WIDGET_ATTRS)

    def clean(self):
        cleaned_data = self.cleaned_data
        ip = cleaned_data.get('ip')
        cat = cleaned_data.get('category')
        ro = cleaned_data.get('read_only')
        self.snmp_version = '1'

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

class NetboxStep3(forms.ModelForm):
    serial = forms.CharField(required=False)

    class Meta:
        model = Netbox
        fields = ('ip', 'sysname', 'category', 'read_only', 'read_write',
        'room', 'organization', 'snmp_version', 'type')

    def __init__(self, data=None, *args, **kwargs):
        super(NetboxStep3, self).__init__(data, *args, **kwargs)
        data = data or {}
        initial = kwargs.get('initial', {})
        if initial or data:
            cat = initial.get('category') or data.get('category')
            subcat = Subcategory.objects.filter(category=cat).order_by('id')
            if subcat.count() > 0:
                self.fields['subcategories'] = forms.ModelMultipleChoiceField(subcat, required=False)

            serial = initial.get('serial') or data.get('serial')
            if serial:
                self.fields['serial'].widget = forms.TextInput(attrs=READONLY_WIDGET_ATTRS)

        readonly_field_names = (
            'ip', 'room', 'sysname', 'category', 'organization', 'read_only',
            'read_write', 'snmp_version')
        for field_name in readonly_field_names:
            self.fields[field_name].widget = forms.TextInput(attrs=READONLY_WIDGET_ATTRS)
        self.fields['type'].widget = forms.HiddenInput()

    def clean_serial(self):
        serial = self.cleaned_data['serial']
        try:
            netbox = Netbox.objects.get(device__serial=serial)
        except Netbox.DoesNotExist:
            return serial
        else:
            raise forms.ValidationError("Serial exists in database")

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

class PrefixForm(forms.ModelForm):
    class Meta:
        model = Prefix

class CablingForm(forms.ModelForm):
    class Meta:
        model = Cabling

class PatchForm(forms.ModelForm):
    class Meta:
        model = Patch

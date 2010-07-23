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

from django import forms

from nav.Snmp import Snmp, TimeOutException, SnmpError
from nav.models.cabling import Cabling, Patch
from nav.models.manage import Netbox, NetboxType, Room, Location, Organization, Usage, Vendor, Subcategory, Vlan, Prefix, Category
from nav.models.service import Service

class NetboxSysnameForm(forms.Form):
    name = forms.CharField()
    category = forms.ModelChoiceField(Category.objects.all())
    read_only = forms.CharField(required=False)
    read_write = forms.CharField(required=False)
    room = forms.ModelChoiceField(Room.objects.all())
    organiztion = forms.ModelChoiceField(Organization.objects.all())
    step = forms.IntegerField(initial=0, widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = self.cleaned_data
        name = cleaned_data.get('name')
        cat = cleaned_data.get('category')
        ro = cleaned_data.get('read_only')

        if cat and cat.req_snmp and not ro:
            self._errors['read_only'] = self.error_class(["Category %s requires Read Only community." % cat.id])
            del cleaned_data['category']
            del cleaned_data['read_only']

        if ro and name:
            self.snmp_version = False
            try:
                try:
                    snmp = Snmp(name, ro, '2c')
                    sysname = snmp.get('1.3.6.1.2.1.1.5.0')
                    self.snmp_version = '2c'
                except TimeOutException:
                    snmp = Snmp(name, ro, '1')
                    sysname = snmp.get('1.3.6.1.2.1.1.5.0')
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

class NetboxMetaForm(forms.ModelForm):
    step = forms.IntegerField(initial=1, widget=forms.HiddenInput)

    class Meta:
        model = Netbox
        fields = ('room', 'type', 'category', 'organization')

class NetboxSubcatForm(forms.ModelForm):
    step = forms.IntegerField(initial=2, widget=forms.HiddenInput)

    class Meta:
        model = Netbox
        fields = ('subcategories')

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

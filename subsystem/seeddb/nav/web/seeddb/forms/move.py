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

class MoveOperationForm(forms.Form):
    """Generates a form with checkboxes for each field in the supplied form.
    """
    def __init__(self, *args, **kwargs):
        form = kwargs.pop('form', None)
        hidden = kwargs.pop('hidden', False)

        super(MoveOperationForm, self).__init__(*args, **kwargs)

        fields = form.fields.keys()
        for field in fields:
            key = 'operation_%s' % field
            self.fields[key] = forms.BooleanField(required=False, label="Change %s" % field)
            if hidden:
                self.fields[key].widget = forms.HiddenInput()

    def clean(self):
        clean = [key for key in self.cleaned_data if self.cleaned_data[key]]
        if len(clean) == 0:
            raise forms.ValidationError("You must select at least one foreign key to edit.")
        return self.cleaned_data

class MoveForm(forms.Form):
    """Parent class for move forms.

    If a MoveOperationForm instance with cleaned data is passed in the
    'operation_form' argument the resulting form will omitt the fields that was
    not selected in the MoveOperationForm.
    """
    def __init__(self, *args, **kwargs):
        op_form = None
        if kwargs:
            op_form = kwargs.pop('operation_form')
        super(MoveForm, self).__init__(*args, **kwargs)
        if op_form:
            data = op_form.cleaned_data
            active_fields = [key.split("_")[1] for key in data if data[key]]
            for key in self.fields:
                if key not in active_fields:
                    del self.fields[key]

class NetboxMoveForm(MoveForm):
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all())
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all())

class RoomMoveForm(MoveForm):
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all())

class OrganizationMoveForm(MoveForm):
    parent = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)

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

class MoveWidget(forms.MultiWidget):
    def __init__(self, attrs=None, choices=[]):
        widgets = (
            forms.CheckboxInput(attrs=attrs),
            forms.Select(attrs=attrs, choices=choices),
        )
        super(MoveWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if not value:
            return [False, None]
        else:
            return [True, value]

    def format_output(self, widgets):
        return u'Do change %s and stuff %s' % (widgets[0], widgets[1])

class HiddenMoveWidget(forms.MultiWidget):
    def __init__(self, attrs=None, choices=[]):
        widgets = (
            forms.HiddenInput(attrs=attrs),
            forms.HiddenInput(attrs=attrs),
        )

    def decompress(self, value):
        if not value:
            return [False, None]
        else:
            return [True, value]

class MoveField(forms.MultiValueField):
    hidden_widget = HiddenMoveWidget

    def __init__(self, choices=None, *args, **kwargs):
        empty_choice = [(u'', u'----------')]
        widget_choices = empty_choice + [(option.pk, option) for option in choices]

        widget = MoveWidget(attrs=None, choices=widget_choices)
        fields = (
            forms.BooleanField(),
            forms.ModelChoiceField(choices),
        )
        super(MoveField, self).__init__(fields, widget=widget, *args, **kwargs)

    def compress(self, data_list):
        """Returns the selected value if the checbox is selected.
        False if the checkbox is not selected.
        """
        edit_checkbox = data_list[0]
        if edit_checkbox:
            new_value = data_list[1]
            # TODO
            # Some fields can be NULL, some can not
            return new_value
        else:
            return False

    def clean(self, value):
        cleaned = super(MoveField, self).clean(value)
        if cleaned in ("", None):
            raise forms.ValidationError(self.error_messages['required'])
        return cleaned

class RoomMoveForm(forms.Form):
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all())

class NetboxMoveOperationForm(forms.Form):
    room = forms.BooleanField(required=False)
    organization = forms.BooleanField(required=False)

class MoveOperationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        form = kwargs.pop('form', None)
        super(MoveOperationForm, self).__init__(*args, **kwargs)
        fields = form.fields.keys()
        for field in fields:
            self.fields[field] = forms.BooleanField(required=False)

class NetboxMoveForm(forms.Form):
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)

    def __init__(self, operation_form=None, *args, **kwargs):
        super(NetboxMoveForm, self).__init__(*args, **kwargs)

        if operation_form:
            op_form_data = operation_form.cleaned_data
            active_fields = [key for key in op_form_data if op_form_data[key]]
            for key in self.fields:
                if key not in active_fields:
                    del self.fields[key]

#class NetboxMoveForm(forms.Form):
#    room = MoveField(choices=Room.objects.order_by('id').all(), required=False)
#    organization = MoveField(choices=Organization.objects.order_by('id').all(), required=False)

#    def clean(self):
#        data = self.cleaned_data
#        if not data['room'] and data['room'] != False:
#            raise forms.ValidationError("It's liek empty dood")
#
#        data = self.cleaned_data
#        room = data['room']
#        organization = data['organization']
#
#        if not room and not organization:
#            raise forms.ValidationError("Organiztion and/or room must be selected.")
#        return data

class OrganizationMoveForm(forms.Form):
    parent = forms.ModelChoiceField(
        Organization.objects.order_by('id').all())

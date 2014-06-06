#
# Copyright (C) 2014 UNINETT AS
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
# pylint: disable=C1001,R0903
"""Forms for seeddb pages"""

from django import forms
from django_hstore.forms import DictionaryField

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Fieldset, Row, Column,
                                            Submit)

from nav.web.crispyforms import LabelSubmit
from nav.models.manage import (Location, Room, Organization, NetboxType,
                               Vendor)
from nav.models.cabling import Cabling


def get_formhelper():
    """Get the default formhelper for seeddb forms"""
    helper = FormHelper()
    helper.form_action = ''
    helper.form_method = 'GET'
    helper.form_class = 'custom'
    return helper


def get_layout(heading, rows):
    """Get the default layout for filterforms

    :type heading: basestring
    :type rows: list
    """
    return Layout(Fieldset(heading, Row(*rows)))


def get_single_layout(heading, row):
    """Get default layout for a single filter"""
    return get_layout(heading,  [
        Column(row, css_class='medium-8'),
        Column(get_submit_button(), css_class='medium-4')
    ])


def get_submit_button(value='Filter'):
    """Get default submit button for seeddb filter forms"""
    return LabelSubmit('submit', value, css_class='postfix')


class RoomFilterForm(forms.Form):
    """Form for filtering rooms"""
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all(), required=False)

    def __init__(self, *args, **kwargs):
        super(RoomFilterForm, self).__init__(*args, **kwargs)
        self.helper = get_formhelper()
        self.helper.layout = get_single_layout('Filter rooms', 'location')


class RoomForm(forms.ModelForm):
    """Form for editing/adding rooms"""
    location = forms.ModelChoiceField(queryset=Location.objects.order_by('id'))
    data = DictionaryField(widget=forms.Textarea(), label='Attributes',
                           required=False)

    class Meta:
        model = Room


class RoomMoveForm(forms.Form):
    """Form for moving a room to a new location"""
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all(), required=False)


class OrganizationFilterForm(forms.Form):
    """Form for filtering organizations by parent"""
    parent = forms.ModelChoiceField(
        Organization.objects.filter(
            pk__in=Organization.objects.filter(
                parent__isnull=False
            ).values_list('parent', flat=True)
        ).order_by('id'), required=False)

    def __init__(self, *args, **kwargs):
        super(OrganizationFilterForm, self).__init__(*args, **kwargs)
        self.helper = get_formhelper()
        self.helper.layout = get_single_layout('Filter organizations',
                                               'parent')


class OrganizationForm(forms.ModelForm):
    """Form for editing an organization"""
    parent = forms.ModelChoiceField(
        queryset=Organization.objects.order_by('id'),
        required=False)
    data = DictionaryField(widget=forms.Textarea(), label='Attributes',
                           required=False)

    class Meta:
        model = Organization

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            # disallow editing the primary key of existing record
            del self.fields['id']
            # remove self from list of selectable parents
            parent = self.fields['parent']
            parent.queryset = parent.queryset.exclude(
                id=kwargs['instance'].id)


class OrganizationMoveForm(forms.Form):
    """Form for moving an organization to another parent"""
    parent = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)


class NetboxTypeFilterForm(forms.Form):
    """Form for filtering a netbox type by vendor"""
    vendor = forms.ModelChoiceField(
        Vendor.objects.order_by('id').all(), required=False)

    def __init__(self, *args, **kwargs):
        super(NetboxTypeFilterForm, self).__init__(*args, **kwargs)
        self.helper = get_formhelper()
        self.helper.layout = get_single_layout('Filter types', 'vendor')


class NetboxTypeForm(forms.ModelForm):
    """Form for editing a netbox type"""
    class Meta:
        model = NetboxType


class CablingFilterForm(forms.Form):
    """Form for filtering cabling by room"""
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)

    def __init__(self, *args, **kwargs):
        super(CablingFilterForm, self).__init__(*args, **kwargs)
        self.helper = get_formhelper()
        self.helper.layout = get_single_layout('Filter cabling', 'room')


class CablingForm(forms.ModelForm):
    """Form for editing a cabling instance"""
    class Meta:
        model = Cabling

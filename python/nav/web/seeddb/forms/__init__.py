# -*- coding: utf-8 -*-#
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
from django.utils.safestring import mark_safe

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Fieldset, Row, Column,
                                            Submit)

from nav.web.crispyforms import LabelSubmit
from nav.models.manage import (Location, Room, Organization, NetboxType,
                               Vendor, NetboxGroup, Category, Netbox)
from nav.models.cabling import Cabling

import logging
_logger = logging.getLogger(__name__)


def create_hierarchy(klass):
    """Creates a tree structure for select choices
    
    This is used in forms that use Organization and Location fields, and will
    visualize the tree structure of the data.
    """
    roots = klass.objects.filter(parent__isnull=True).order_by('id')
    choices = []
    for root in roots:
        create_choices(root, choices)
    return choices


def create_choices(element, choices, last=False):
    """Recursively create and pad the choices for each element"""
    choices.append((element.pk,
         tree_pad(unicode(element.pk),
                  element.num_ancestors(), last=last)))

    children = element.get_children()
    num_children = len(children)
    for index, child in enumerate(children):
        if index == num_children - 1:
            create_choices(child, choices, last=True)
        else:
            create_choices(child, choices)
            

def tree_pad(string, level=0, last=False):
    """Pad the string according to level and if its last"""
    if level:
        if last:
            string = "&#9492; " + string  # └
        else:
            string = "&#9500; " + string  # ├
        for _ in range(level-1):
            string = "&#9474; " + string  # │
    return mark_safe(string)


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
    return get_layout(heading, [
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
    location = forms.ChoiceField(choices=create_hierarchy(Location))
    data = DictionaryField(widget=forms.Textarea(), label='Attributes',
                           required=False)

    class Meta(object):
        model = Room
        fields = '__all__'

    def clean_location(self):
        data = self.cleaned_data.get('location')
        return Location.objects.get(pk=data)


class RoomMoveForm(forms.Form):
    """Form for moving a room to a new location"""
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all(), required=False)


class LocationForm(forms.ModelForm):
    """Form for editing and adding a location"""
    parent = forms.ModelChoiceField(
        queryset=Location.objects.order_by('id'),
        required=False)
    data = DictionaryField(widget=forms.Textarea(), label='Attributes',
                           required=False)

    class Meta(object):
        model = Location
        fields = ('parent', 'id', 'description', 'data')

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            # disallow editing the primary key of existing record
            del self.fields['id']
            # remove self from list of selectable parents
            parent = self.fields['parent']
            parent.queryset = parent.queryset.exclude(
                id=kwargs['instance'].id)


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

    class Meta(object):
        model = Organization
        fields = '__all__'

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
    class Meta(object):
        model = NetboxType
        fields = '__all__'


class CablingForm(forms.ModelForm):
    """Form for editing a cabling instance"""
    class Meta(object):
        model = Cabling
        fields = '__all__'
        widgets = {
            'room': forms.Select(attrs={'class': 'select2'})
        }


class DeviceGroupForm(forms.ModelForm):
    """Form for editing a device group

    We need to create the netboxes field for the many to many relationship, as
    this is only created by Django on modelforms based on the model where the
    field is defined (in this case nav.models.manage.Netbox).
    """
    netboxes = forms.ModelMultipleChoiceField(
        queryset=Netbox.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        # If the form is based on an existing model instance, populate the
        # netboxes field with netboxes from the many to many relationship
        if 'instance' in kwargs and kwargs['instance'] is not None:
            initial = kwargs.setdefault('initial', {})
            initial['netboxes'] = [n.pk for n in
                                   kwargs['instance'].netbox_set.all()]
        forms.ModelForm.__init__(self, *args, **kwargs)

    class Meta(object):
        model = NetboxGroup
        fields = '__all__'


def to_choice_format(objects, key, value):
    """Return a list of tuples from model given key and value"""
    return [(getattr(obj, key), getattr(obj, value)) for obj in objects]


def get_netboxes_in_group(group):
    if group:
        return group.netbox_set.all()
    else:
        return Netbox.objects.none()


def get_netboxes_not_in_group(group):
    if group:
        return Netbox.objects.exclude(
            pk__in=group.netbox_set.all().values_list('id', flat=True))
    else:
        return Netbox.objects.all()

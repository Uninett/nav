# -*- coding: utf-8 -*-#
# Copyright (C) 2014 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Forms for seeddb pages"""

import logging

from django import forms
from django.utils.safestring import mark_safe

from nav.django.forms import HStoreField
from nav.models.manage import (
    Location,
    Room,
    Organization,
    NetboxType,
    Vendor,
    NetboxGroup,
    Netbox,
)
from nav.models.cabling import Cabling
from nav.oids import OID
from nav.web.crispyforms import (
    FlatFieldset,
    FormColumn,
    FormRow,
    SubmitField,
    set_flat_form_attributes,
)

_logger = logging.getLogger(__name__)


BOX_CHARS = {
    'SPACE': '&nbsp;',
    'VERTICAL': '&#9474;',  # │
    'UP_AND_RIGHT': '&#9492;',  # └
    'VERTICAL_AND_RIGHT': '&#9500;',  # ├
}
SEPARATOR = "."


def create_hierarchy(klass):
    """Creates a tree structure for select choices

    This is used in forms that use Organization and Location fields, and will
    visualize the tree structure of the data.
    """
    roots = klass.objects.filter(parent__isnull=True).order_by('id')
    choices = [('', '---------')]
    for index, root in enumerate(roots):
        is_last_root = index == roots.count() - 1
        ancestors = []
        choices = choices + create_choices(root, ancestors, is_last_root)
    return choices


def create_choices(element, ancestors, is_last_child=False):
    """Recursively create a choice for the element and its children

    :param element: a model instance using the TreeMixin
    :param ancestors: list of booleans for each ancestor, indicating if that
                      ancestor was the last child
    :param is_last_child: indicates if this is the last child

    :returns: a list of tuples meant to be used as choices in a form select. The
              string element is padded to indicate placement in a tree-structure
    """
    choices = [(element.pk, tree_pad(str(element.pk), ancestors, last=is_last_child))]
    child_ancestors = ancestors + [is_last_child]
    children = element.get_children()
    num_children = children.count()
    for index, child in enumerate(children):
        last = index == num_children - 1
        choices = choices + create_choices(child, child_ancestors, is_last_child=last)

    return choices


def tree_pad(string, ancestors, last=False):
    """Pad the string according to ancestors and position

    :param ancestors: a list of booleans for each ancestor. The value indicates
                      if this ancestor was the last child
    :param last: indicates if this is the last child

    :returns: a string (marked safe) representing an option in a dropdown,
              drawing it's part of the tree-structure
    """
    charmap = {
        True: BOX_CHARS['UP_AND_RIGHT'] + BOX_CHARS['SPACE'],  # └
        False: BOX_CHARS['VERTICAL_AND_RIGHT'] + BOX_CHARS['SPACE'],  # ├
    }

    if ancestors:
        string = "".join([get_prefix(ancestors), charmap[last], string])
    return mark_safe(string)


def get_prefix(ancestors):
    """Adds characters based on ancestor last child status"""
    charmap = {
        True: 2 * BOX_CHARS['SPACE'],  # double space
        False: BOX_CHARS['VERTICAL'] + BOX_CHARS['SPACE'],  # │
    }
    return "".join([charmap[x] for x in ancestors[1:]])


def cut_branch(field, klass, pk):
    """Filter choices for a field based on descendants of an instance"""
    descendants = klass.objects.get(pk=pk).get_descendants(include_self=True)
    descendant_ids = [d.pk for d in descendants]
    return [c for c in field.choices if c[0] not in descendant_ids]


# helpers


def get_single_layout(heading, filter_field):
    """Get default layout for a single filter"""
    return set_flat_form_attributes(
        form_class="custom",
        form_method="get",
        form_fields=[
            FlatFieldset(
                legend=heading,
                fields=[
                    FormRow(
                        fields=[
                            FormColumn(fields=[filter_field], css_classes="medium-8"),
                            FormColumn(
                                fields=[
                                    SubmitField(
                                        value="Filter",
                                        css_classes="postfix",
                                        has_empty_label=True,
                                    )
                                ],
                                css_classes="medium-4",
                            ),
                        ]
                    )
                ],
            )
        ],
    )


# forms


class RoomFilterForm(forms.Form):
    """Form for filtering rooms"""

    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all(), required=False
    )
    location.widget.attrs.update({"class": "select"})

    def __init__(self, *args, **kwargs):
        super(RoomFilterForm, self).__init__(*args, **kwargs)
        self.attrs = get_single_layout(
            heading="Filter rooms", filter_field=self["location"]
        )


class RoomForm(forms.ModelForm):
    """Form for editing/adding rooms"""

    location = forms.ChoiceField(choices=())
    data = HStoreField(label='Attributes', required=False)

    def __init__(self, *args, **kwargs):
        super(RoomForm, self).__init__(*args, **kwargs)
        self.fields['location'].choices = create_hierarchy(Location)
        if self.instance and self.instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True

    class Meta(object):
        model = Room
        fields = '__all__'

    def clean_location(self):
        data = self.cleaned_data.get('location')
        return Location.objects.get(pk=data)


class RoomMoveForm(forms.Form):
    """Form for moving a room to a new location"""

    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all(), required=False
    )


class LocationForm(forms.ModelForm):
    """Form for editing and adding a location"""

    parent = forms.ChoiceField(required=False)
    data = HStoreField(label='Attributes', required=False)

    class Meta(object):
        model = Location
        fields = ('parent', 'id', 'description', 'data')

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        field = self.fields['parent']
        field.choices = create_hierarchy(Location)

        if self.instance.id:
            # disallow editing the primary key of existing record
            del self.fields['id']
            # remove self and all descendants from list of selectable parents
            field.choices = cut_branch(field, Location, self.instance.id)

    def clean_parent(self):
        """Provide a model as the parent.

        This is needed because we use a normal ChoiceField (because of the tree
        structure) that does not provide a model instance when selected.
        """
        parent = self.cleaned_data.get('parent')
        if parent:
            return Location.objects.get(pk=parent)
        else:
            # Explicitly return None because no parent is an empty string and
            # thus we need to return None not the empty string
            return None


class OrganizationForm(forms.ModelForm):
    """Form for editing an organization"""

    parent = forms.ChoiceField(required=False)
    data = HStoreField(label='Attributes', required=False)

    class Meta(object):
        model = Organization
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(OrganizationForm, self).__init__(*args, **kwargs)
        field = self.fields['parent']
        field.choices = create_hierarchy(Organization)

        if self.instance.id:
            # disallow editing the primary key of existing record
            del self.fields['id']
            # remove self and all descendants from list of selectable parents
            field.choices = cut_branch(field, Organization, self.instance.id)

    def clean_parent(self):
        """Provide a model as the parent.

        This is needed because we use a normal ChoiceField (because of the tree
        structure) that does not provide a model instance when selected.
        """
        parent = self.cleaned_data.get('parent')
        if parent:
            return Organization.objects.get(pk=parent)
        else:
            # Explicitly return None because no parent is an empty string and
            # thus we need to return None, not the empty string
            return None


class OrganizationMoveForm(forms.Form):
    """Form for moving an organization to another parent"""

    parent = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False
    )


class NetboxTypeFilterForm(forms.Form):
    """Form for filtering a netbox type by vendor"""

    vendor = forms.ModelChoiceField(Vendor.objects.order_by('id').all(), required=False)

    def __init__(self, *args, **kwargs):
        super(NetboxTypeFilterForm, self).__init__(*args, **kwargs)
        self.attrs = get_single_layout(
            heading="Filter types", filter_field=self["vendor"]
        )


class NetboxTypeForm(forms.ModelForm):
    """Form for editing a netbox type"""

    class Meta(object):
        model = NetboxType
        fields = '__all__'

    def clean_sysobjectid(self):
        sysobjectid = self.cleaned_data.get('sysobjectid')
        try:
            sysobjectid_oid = OID(sysobjectid)
        except ValueError:
            raise forms.ValidationError(
                "Sysobjectid can only contain digits and periods."
            )
        else:
            return str(sysobjectid_oid).strip(SEPARATOR)


class CablingForm(forms.ModelForm):
    """Form for editing a cabling instance"""

    class Meta(object):
        model = Cabling
        fields = '__all__'
        widgets = {'room': forms.Select(attrs={'class': 'select2'})}


class DeviceGroupForm(forms.ModelForm):
    """Form for editing a device group

    We need to create the netboxes field for the many to many relationship, as
    this is only created by Django on modelforms based on the model where the
    field is defined (in this case nav.models.manage.Netbox).
    """

    netboxes = forms.ModelMultipleChoiceField(
        queryset=Netbox.objects.all(), required=False
    )
    netboxes.widget.attrs.update({"class": "select2"})

    def __init__(self, *args, **kwargs):
        # If the form is based on an existing model instance, populate the
        # netboxes field with netboxes from the many to many relationship
        if 'instance' in kwargs and kwargs['instance'] is not None:
            initial = kwargs.setdefault('initial', {})
            initial['netboxes'] = [n.pk for n in kwargs['instance'].netboxes.all()]
        forms.ModelForm.__init__(self, *args, **kwargs)

    class Meta(object):
        model = NetboxGroup
        fields = '__all__'


def to_choice_format(objects, key, value):
    """Return a list of tuples from model given key and value"""
    return [(getattr(obj, key), getattr(obj, value)) for obj in objects]


def get_netboxes_in_group(group):
    if group:
        return group.netboxes.all()
    else:
        return Netbox.objects.none()


def get_netboxes_not_in_group(group):
    if group:
        return Netbox.objects.exclude(
            pk__in=group.netboxes.all().values_list('id', flat=True)
        )
    else:
        return Netbox.objects.all()

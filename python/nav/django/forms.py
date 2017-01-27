#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django form field types for NAV"""

from django import forms
from django.db import models
from django.utils.text import capfirst
from django.core import exceptions

from nav.util import is_valid_cidr
from nav.django import validators, widgets


class CIDRField(forms.CharField):
    """CIDR address text field with validation"""

    def clean(self, value):
        if value and not is_valid_cidr(value):
            raise forms.ValidationError(
                "Value must be a valid CIDR address")
        else:
            return super(CIDRField, self).clean(value)


class PointField(forms.CharField):
    widget = widgets.PointInput

    def clean(self, value):
        if not value or validators.is_valid_point_string(value):
            return super(PointField, self).clean(value)
        raise forms.ValidationError(
            "Invalid format. Point field format is '(x,y)'.")


class MultiSelectFormField(forms.MultipleChoiceField):
    """
    Usually you want to store multiple choices as a manytomany link to
    another table. Sometimes however it is useful to store them in the model
    itself. This field implements a model field and an accompanying
    formfield to store multiple choices as a comma-separated list of
    values, using the normal CHOICES attribute.

    You'll need to set maxlength long enough to cope with the maximum number of
    choices, plus a comma for each.

    The normal get_FOO_display() method returns a comma-delimited string of the
    expanded values of the selected choices.

    The formfield takes an optional max_choices parameter to validate a maximum
    number of choices.

    original author, Daniel Roseman, public domain
    Snippet from http://djangosnippets.org/snippets/2753/
    """
    widget = forms.CheckboxSelectMultiple

    def __init__(self, *args, **kwargs):
        self.max_choices = kwargs.pop('max_choices', 0)
        super(MultiSelectFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value and self.required:
            raise forms.ValidationError(self.error_messages['required'])
            # if value and self.max_choices and len(value) > self.max_choices:
        #     raise forms.ValidationError('You must select a maximum of %s
        # choice%s.'
        #             % (apnumber(self.max_choices),
        # pluralize(self.max_choices)))
        return value


class MultiSelectField(models.Field):
    """
    Usually you want to store multiple choices as a manytomany link to
    another table. Sometimes however it is useful to store them in the model
    itself. This field implements a model field and an accompanying
    formfield to store multiple choices as a comma-separated list of
    values, using the normal CHOICES attribute.

    You'll need to set maxlength long enough to cope with the maximum number of
    choices, plus a comma for each.

    The normal get_FOO_display() method returns a comma-delimited string of the
    expanded values of the selected choices.

    The formfield takes an optional max_choices parameter to validate a maximum
    number of choices.

    original author, Daniel Roseman, public domain
    Snippet from http://djangosnippets.org/snippets/2753/
    """

    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "CharField"

    def get_choices_default(self):
        return self.get_choices(include_blank=False)

    def _get_FIELD_display(self, field):
        value = getattr(self, field.attname)
        choicedict = dict(field.choices)

    def formfield(self, **kwargs):
        # don't call super, as that overrides default widget if it has choices
        defaults = {'required': not self.blank,
                    'label': capfirst(self.verbose_name),
                    'help_text': self.help_text, 'choices': self.choices}
        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)
        return MultiSelectFormField(**defaults)

    def get_prep_value(self, value):
        return value

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if isinstance(value, basestring):
            return value
        elif isinstance(value, list):
            return ",".join(value)

    def to_python(self, value):
        if value is not None:
            return value if isinstance(value, list) else value.split(',')
        return ''

    def contribute_to_class(self, cls, name):
        super(MultiSelectField, self).contribute_to_class(cls, name)
        if self.choices:
            func = lambda self, fieldname=name,\
                          choicedict=dict(self.choices): ",".join(
                [choicedict.get(value, value) for value in
                 getattr(self, fieldname)])
            setattr(cls, 'get_%s_display' % self.name, func)

    def validate(self, value, model_instance):
        arr_choices = self.get_choices_selected(self.get_choices_default())
        for opt_select in value:
            if (int(
                opt_select) not in arr_choices):  # the int() here is for
                # comparing with integer choices
                raise exceptions.ValidationError(
                    self.error_messages['invalid_choice'] % value)
        return

    def get_choices_selected(self, arr_choices=''):
        if not arr_choices:
            return False
        list = []
        for choice_selected in arr_choices:
            list.append(choice_selected[0])
        return list

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

        ## todo: when using south, requires the two next lines for
        ## MultiSelectFormField and MultiSelectField to work with south:
        #from south.modelsinspector import add_introspection_rules
        #add_introspection_rules([], ["^coop\.utils\.fields\.MultiSelectField"])

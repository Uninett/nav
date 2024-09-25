#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A collection of forms using the django crispy forms framework"""
from typing import Optional

from django import forms
from crispy_forms.layout import BaseInput
from crispy_forms_foundation.layout import Field, Submit, Button


class NavSubmit(BaseInput):
    """Displays proper Foundation submit button"""

    input_type = 'submit'
    field_classes = 'button small'


class NavButton(Button):
    """A normal nav size button"""

    field_classes = 'button small'


class LabelSubmit(Submit):
    """Submitbutton with a label above it to align within a row"""

    template = 'custom_crispy_templates/submit.html'


class CheckBox(Field):
    """Checkbox suited for the NAV layout"""

    template = 'custom_crispy_templates/horizontal_checkbox.html'


class HelpField(Field):
    """Field that displays an icon with tooltip as helptext"""

    template = 'custom_crispy_templates/field_helptext_as_icon.html'


class NumberInput(forms.TextInput):
    """Input widget with type set to number"""

    input_type = 'number'


class NumberField(forms.IntegerField):
    """Input field with type set to number"""

    widget = NumberInput


# For uncrispyfied forms:


class FlatFieldset:
    template = 'custom_crispy_templates/flat_fieldset.html'


def set_flat_fieldset(legend, fields: list, css_class=''):
    obj = FlatFieldset()
    obj.legend = legend
    obj.fields = fields
    obj.css_class = css_class
    return obj


class SubmitField:
    def __init__(
        self, name: str = 'submit', value: str = 'Submit', css_classes: str = ''
    ):
        self.name = name
        self.value = value
        self.css_classes = css_classes
        self.input_type = 'submit'


def set_flat_form_attributes(
    legend=None,
    form_action='',
    form_method='post',
    submit_field: Optional[SubmitField] = None,
    form_fields: list = None,
):
    class Obj:
        pass

    obj = Obj()
    obj.legend = legend
    obj.action = form_action
    obj.method = form_method
    obj.submit_field = submit_field
    obj.form_fields = form_fields
    return obj

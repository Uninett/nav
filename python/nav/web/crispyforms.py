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
from types import SimpleNamespace
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
    """
    A class representing a fieldset for forms.
    Only flat layout of children fields is supported out of the box.
    Any nesting of fields inside this fieldset might require custom
    class definitions akin to this one.

    Attributes:
        template (str): The path to the template used for rendering the fieldset.
        Path is relative to the app's templates directory.
        legend (str): The legend text for the fieldset.
        fields (list): A list of fields to include in the fieldset.
        css_class (str): Additional CSS classes to apply to the fieldset.
    """

    template = 'custom_crispy_templates/flat_fieldset.html'

    def __init__(self, legend, fields: list, css_class=''):
        """
        Initializes a FlatFieldset object with the specified attributes.

        Args:
            legend (str): The legend text for the fieldset.
            fields (list): A list of fields to include in the fieldset.
            css_class (str, optional): Additional CSS classes to apply to the fieldset. Defaults to an empty string.
        """
        self.legend = legend
        self.fields = fields
        self.css_class = css_class
        self.template = FlatFieldset.template


class SubmitField:
    """
    A class representing a submit field (button) in a form.

    Attributes:
        name (str): The name attribute of the submit field.
        value (str): The display text of the submit button.
        css_classes (str): Additional CSS classes to apply to the submit button.
        input_type (str): The type of input, which is 'submit' for this class.
    """

    def __init__(
        self, name: str = 'submit', value: str = 'Submit', css_classes: str = ''
    ):
        """
        Initializes a SubmitField object with the specified attributes.

        Args:
            name (str, optional): The name attribute of the submit field. Defaults to 'submit'.
            value (str, optional): The display text of the submit button. Defaults to 'Submit'.
            css_classes (str, optional): Additional CSS classes to apply to the submit button. Defaults to an empty string.
        """
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
    """
    Sets and returns a SimpleNamespace object representing a flat form.
    Only flat layout of children fields is supported out of the box.
    Any nesting of fields inside this form might require custom
    class and template definitions.

    Args:
        legend (str, optional): The legend text for the form. Defaults to None.
        form_action (str, optional): The action destination URL for the form. Defaults to an empty string.
        form_method (str, optional): The HTTP method for the form. Defaults to 'post'.
        submit_field (SubmitField, optional): An instance of SubmitField for the form's submit button. Defaults to None.
        form_fields (list, optional): A list of fields to include in the form in case you want to render any fields
        that are not present in Django's built-in Field classes, f.e. fieldset, submit, row, column etc.
        Do not set it if you want to render only Django's built-in fields. Defaults to None.

    Returns:
        SimpleNamespace: An object containing the form attributes.
    """

    return SimpleNamespace(
        legend=legend,
        action=form_action,
        method=form_method,
        submit_field=submit_field,
        form_fields=form_fields,
    )

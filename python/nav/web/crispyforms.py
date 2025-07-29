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
"""A collection of forms inspired by the django crispy forms framework"""

from types import SimpleNamespace
from typing import Optional

from django import forms


class CheckBox:
    """Checkbox suited for the NAV layout

    :param field: A field to render as a checkbox field.
    """

    def __init__(self, field, css_classes: Optional[str] = None):
        self.field = field
        self.css_classes = css_classes
        self.template = 'custom_crispy_templates/form_checkbox.html'


class HelpFormField:
    """Field that displays an icon with tooltip as helptext

    :param field: A field to render as a help field.
    """

    def __init__(self, field):
        """Constructor method"""
        self.field = field
        self.input_type = 'helpfield'


class NumberInput(forms.TextInput):
    """Input widget with type set to number"""

    input_type = 'number'


class NumberField(forms.IntegerField):
    """Input field with type set to number"""

    widget = NumberInput


class FlatFieldset:
    """A class representing a fieldset for forms.
    Only flat layout of children fields is supported out of the box.
    Any nesting of fields inside this fieldset might require custom
    class definitions akin to this one.

    :param legend: The legend text for the fieldset.
    :type legend: str
    :param fields: A list of fields to include in the fieldset.
    :param css_class: Additional CSS classes to apply to the fieldset.
    :param template: The path to the template used for rendering the fieldset.
    Path is relative to the app's templates directory.
    """

    def __init__(
        self,
        legend,
        fields: list,
        css_class='',
        template: str = 'custom_crispy_templates/flat_fieldset.html',
    ):
        """Constructor method"""
        self.legend = legend
        self.fields = fields
        self.css_class = css_class
        self.template = template


class FormRow:
    """A class representing a row in a form layout.
    Row is not a functional element in forms, but a visual one.

    :param fields: A list of fields to include in the row.
    :param css_classes: Additional CSS classes to apply to the row. Defaults to an
    empty string.
    """

    def __init__(self, fields: list, css_classes: Optional[str] = None):
        """Constructor method"""
        self.fields = fields
        self.css_classes = css_classes
        self.template = 'custom_crispy_templates/form_row.html'


class FormColumn:
    """A class representing a column in a form layout.
    Column is not a functional element in forms, but a visual one.

    :param fields: A list of fields to include in the column.
    :param css_classes: Additional CSS classes to apply to the column. Defaults to
    an empty string.
    """

    def __init__(self, fields: list, css_classes: str = ''):
        """Constructor method"""
        self.fields = fields
        self.css_classes = css_classes
        self.template = 'custom_crispy_templates/form_column.html'


class SubmitField:
    """A class representing a submit field (button) in a form.

    :param name: The name attribute of the submit field.
    :param value: The display text of the submit button.
    :param css_classes: Additional CSS classes to apply to the submit button.
    :param has_empty_label: If an empty label is added above the submit button to align
    it within a row.
    :ivar input_type: The type of input, which is 'submit' for this class.
    :type input_type: str
    """

    def __init__(
        self,
        name: str = 'submit',
        value: str = 'Submit',
        css_classes: str = '',
        has_empty_label: bool = False,
    ):
        """Constructor method"""
        self.name = name
        self.value = value
        self.css_classes = css_classes
        self.has_empty_label = has_empty_label
        self.input_type = 'submit'


def set_flat_form_attributes(
    legend=None,
    form_action='',
    form_method='post',
    submit_field: Optional[SubmitField] = None,
    form_fields: list = None,
    form_id: str = '',
    form_class: str = '',
):
    """Sets and returns a SimpleNamespace object representing a flat form.
    Only flat layout of children fields is supported out of the box.
    Any nesting of fields inside this form might require custom
    class and template definitions.

    :param legend: The legend text for the form. Defaults to None.
    :type legend: str, optional
    :param form_action: The action destination URL for the form. Defaults to an empty
                        string.
    :type form_action: str, optional
    :param form_method: The HTTP method for the form. Defaults to 'post'.
    :type form_method: str, optional
    :param submit_field: An instance of SubmitField for the form's submit button.
                         Defaults to None.
    :param form_fields: A list of fields to include in the form in case you want to
                        render any fields that are not present in Django's built-in
                        Field classes, e.g., fieldset, submit, row, column etc. Do not
                        set it if you want to render only Django's built-in fields.
                        Defaults to None.
    :param form_id: The ID attribute of the form element. Defaults to an empty string.
    :param form_class: Additional CSS classes to apply to the form. Defaults to an
                       empty string.

    :return: An object containing the form attributes.
    :rtype: SimpleNamespace
    """

    return SimpleNamespace(
        legend=legend,
        action=form_action,
        method=form_method,
        submit_field=submit_field,
        form_fields=form_fields,
        form_id=form_id,
        form_class=form_class,
    )


class FormDiv:
    """A class representing a div in a form layout.

    :param fields: A list of fields to include in the div.
    :param css_classes: Additional CSS classes to apply to the div.
    """

    def __init__(
        self, fields: Optional[list] = None, css_classes: Optional[str] = None
    ):
        self.fields = fields
        self.css_classes = css_classes
        self.template = 'custom_crispy_templates/form_div.html'

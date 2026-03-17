#
# Copyright (C) 2011, 2018 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django form field types for NAV"""

import json

from django import forms
from django.core.exceptions import ValidationError
from django.forms import Field, Textarea

from nav.util import is_valid_cidr
from nav.django import validators, widgets

MAX_ALIAS_LENGTH = 64


class CIDRField(forms.CharField):
    """CIDR address text field with validation"""

    def clean(self, value):
        if value and not is_valid_cidr(value):
            raise forms.ValidationError("Value must be a valid CIDR address")
        else:
            return super(CIDRField, self).clean(value)


class PointField(forms.CharField):
    widget = widgets.PointInput

    def clean(self, value):
        if not value or validators.is_valid_point_string(value):
            return super(PointField, self).clean(value)
        raise forms.ValidationError("Invalid format. Point field format is '(x,y)'.")


class JSONWidget(Textarea):
    def _render_value(self, value):
        """Convert the value to JSON

        Falsey values are converted to an empty string. Bytestrings are
        considered to be encoded as utf-8 and converted to text."""
        if value and not isinstance(value, str):
            value = json.dumps(
                value, sort_keys=True, indent=4, cls=validators.JSONBytesEncoder
            )
        else:
            value = ''
        return value

    def render(self, name, value, attrs=None, renderer=None):
        """Convert the value to JSON and render in textarea"""
        value = self._render_value(value)
        return super(JSONWidget, self).render(name, value, attrs, renderer)


class HStoreField(Field):
    def __init__(self, **params):
        params['widget'] = params.get('widget', JSONWidget)
        super(HStoreField, self).__init__(**params)

    def to_python(self, value):
        return validators.validate_hstore(value)


def validate_aliases(aliases: list[str]) -> list[str]:
    """
    Validates a given list of aliases and raises a ValidationError if any of the
    aliases contain the pipe character or are too long

    Returns a deduplicated and stripped version of the given list
    """
    if not aliases:
        return []
    cleaned = []
    for item in aliases:
        if not isinstance(item, str):
            raise ValidationError("All aliases must be strings.")
        stripped = item.strip()
        if "|" in stripped:
            raise ValidationError("Aliases cannot contain the pipe character ('|')")
        if len(stripped) > MAX_ALIAS_LENGTH:
            raise ValidationError(
                f"Alias must be {MAX_ALIAS_LENGTH} characters or fewer."
            )
        if stripped and stripped not in cleaned:
            cleaned.append(stripped)
    return cleaned


class AliasListWidget(forms.Widget):
    """Widget that renders a dynamic list of alias text inputs"""

    template_name = 'seeddb/widgets/alias_list.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if isinstance(value, str):
            value = _parse_json_list(value)
        context['aliases'] = value or []
        return context

    def value_from_datadict(self, data, files, name):
        return _parse_json_list(data.get(f'{name}_json', '[]'))


class AliasListField(forms.Field):
    """Form field for editing a list of alias strings"""

    widget = AliasListWidget

    def __init__(self, *args, verbose_name='entry', **kwargs):
        kwargs.setdefault(
            'help_text',
            "Alternative names that can be used to find"
            f" this {verbose_name} in searches.",
        )
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, str):
            return _parse_json_list(value)
        return value or []

    def clean(self, value):
        return validate_aliases(value)


def _parse_json_list(value):
    """Parse a JSON string as a list, returning [] on failure."""
    try:
        result = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(result, list):
        return []
    return result

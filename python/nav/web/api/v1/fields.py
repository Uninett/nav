#
# Copyright (C) 2019 Uninett AS
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
from rest_framework import serializers


class DisplayNameWritableField(serializers.ChoiceField):
    """A choice field where the display name of the choices can be used for API
    input/output, instead of potentially opaque integers.

    """

    def __init__(self, **kwargs):
        if "choices" not in kwargs:
            kwargs["choices"] = []  # optional, as we can derive it from the model
        super(DisplayNameWritableField, self).__init__(**kwargs)

    def to_representation(self, value):
        return self._choice_map.get(value, value)

    def to_internal_value(self, data):
        try:
            return self._choice_reverse_map[data]
        except KeyError:
            self.fail("invalid_choice", input=data)

    def bind(self, field_name, parent):
        super(DisplayNameWritableField, self).bind(field_name, parent)
        self.choices = parent.Meta.model._meta.get_field(field_name).choices
        self._choice_map = dict(self.choices)
        self._choice_reverse_map = {v: k for (k, v) in self._choice_map.items()}

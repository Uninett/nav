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

from __future__ import unicode_literals, absolute_import

import json
from decimal import Decimal, InvalidOperation

from django.utils.translation import gettext
from django.core.exceptions import ValidationError


def is_valid_point_string(point_string):
    if len(point_string.split(',')) == 2:
        if point_string.startswith('(') and point_string.endswith(')'):
            point_string = point_string[1:-1]
        x_point, y_point = point_string.split(',')
        try:
            Decimal(x_point.strip())
            Decimal(y_point.strip())
        except InvalidOperation:
            pass
        else:
            return True
    return False


class JSONBytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('utf-8')
        return super(JSONBytesEncoder, self).default(self, obj)


def validate_hstore(value):
    """HSTORE validation."""
    # if empty
    if value is None or value == '' or value == 'null':
        value = '{}'

    # ensure valid JSON
    try:
        # work on unicode strings only
        if isinstance(value, bytes):
            value = value.decode('utf-8')

        # convert strings to dictionaries
        if isinstance(value, str):
            dictionary = json.loads(value)

        # if not a string we'll check at the next control if it's a dict
        else:
            dictionary = value
    except ValueError as e:
        raise ValidationError(gettext(u'Invalid JSON: {0}').format(e))

    # ensure is a dictionary
    if not isinstance(dictionary, dict):
        raise ValidationError(gettext(u'No lists or values allowed, only dictionaries'))

    value = json.dumps(dictionary, cls=JSONBytesEncoder)
    dictionary = json.loads(value)

    return dictionary

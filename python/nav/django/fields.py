# Copyright (C) 2018 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import unicode_literals, absolute_import

import json

from django.forms import Field, Textarea
from django.utils import six
from django.utils.translation import ugettext
from django.core.exceptions import ValidationError


def validate_hstore(value):
    """ HSTORE validation. """
    # if empty
    if value is None or value == '' or value == 'null':
        value = '{}'

    # ensure valid JSON
    try:
        # convert strings to dictionaries
        if isinstance(value, six.string_types):
            dictionary = json.loads(value)

        # if not a string we'll check at the next control if it's a dict
        else:
            dictionary = value
    except ValueError as e:
        raise ValidationError(ugettext(u'Invalid JSON: {0}').format(e))

    # ensure is a dictionary
    if not isinstance(dictionary, dict):
        raise ValidationError(ugettext(u'No lists or values allowed, only dictionaries'))

#     # convert any non string object into string
#     for key, value in dictionary.items():
#         if isinstance(value, dict) or isinstance(value, list):
#             dictionary[key] = json.dumps(value)
#         if isinstance(value, bool) or isinstance(value, int) or isinstance(value, float):
#             dictionary[key] = six.text_type(value).lower()
# 
    return dictionary


class HStoreField(Field):

    def __init__(self, **params):
        params['widget'] = params.get('widget', Textarea)
        super(HStoreField, self).__init__(**params)

    def to_python(self, value):
        return validate_hstore(value)

    def render(self, name, value, attrs=None):
        # return json representation of a meaningful value
        # doesn't show anything for None, empty strings or empty dictionaries
        if value and not isinstance(value, six.string_types):
            value = json.dumps(value, sort_keys=True, indent=4)
        return super(HStoreField, self).render(name, value, attrs)

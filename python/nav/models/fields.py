# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 UNINETT AS
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

from datetime import datetime
from decimal import Decimal

from django import forms
from django.db import models, connection
from django.core import exceptions

from nav.util import is_valid_cidr, is_valid_ip
from nav.django import validators, forms as navforms

class DateTimeInfinityField(models.DateTimeField):
    def get_db_prep_value(self, value):
        if value == datetime.max:
            value = u'infinity'
        elif value == datetime.min:
            value = u'-infinity'
        else:
            return super(DateTimeInfinityField, self).get_db_prep_value(value)
        return connection.ops.value_to_db_datetime(value)

class VarcharField(models.TextField):
    def db_type(self):
        return 'varchar'

    def formfield(self, **kwargs):
        defaults = {
            'widget': forms.TextInput,
        }
        defaults.update(kwargs)
        return super(VarcharField, self).formfield(**defaults)

class CIDRField(VarcharField):
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Verifies that the value is a string with a valid CIDR IP address"""
        if value and not is_valid_cidr(value) and not is_valid_ip(value):
            raise exceptions.ValidationError(
                "Value must be a valid CIDR address")
        else:
            return value


class PointField(models.CharField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 100
        super(PointField, self).__init__(*args, **kwargs)

    def db_type(self):
        return 'point'

    def to_python(self, value):
        if not value or isinstance(value, tuple):
            return value
        if isinstance(value, basestring):
            if validators.is_valid_point_string(value):
                noparens = value[1:-1]
                latitude, longitude = noparens.split(',')
                return (Decimal(latitude.strip()), Decimal(longitude.strip()))
        raise exceptions.ValidationError(
            "This value must be a point-string.")

    def get_db_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, tuple):
            return '(%s,%s)' % value

    def formfield(self, **kwargs):
        defaults = {'form_class': navforms.PointField}
        defaults.update(kwargs)
        return super(PointField, self).formfield(**defaults)

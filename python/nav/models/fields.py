# -*- coding: utf-8 -*-
#
# Copyright (C) 2007,2008,2010 UNINETT AS
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

class PointField(models.CharField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 100
        kwargs['blank'] = False
        models.Field.__init__(self, *args, **kwargs)

    def get_internal_type(self):
        return "PointField"

    def to_python(self, value):
        if value is None or isinstance(value, tuple):
            return value
        if isinstance(value, (str, unicode)):
            assert value.startswith('(')
            assert value.endswith(')')
            assert len(value.split(',')) == 2
            noparens = value[1:-1]
            latitude, longitude = noparens.split(',')
            return (Decimal(latitude), Decimal(longitude))
        raise exceptions.ValidationError(
            "This value must be a point-string.")

    def get_db_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, tuple):
            return '(%s,%s)' % tuple

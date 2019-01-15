# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import pickle
import json

from datetime import datetime
from decimal import Decimal

import django
from django import forms
from django.db import models
from django.core import exceptions
from django.db.models import Q
from django.utils import six

try:
    # Django >= 1.8
    from django.apps import apps
    get_models = apps.get_models
    del apps
except ImportError:
    # Django < 1.9
    from django.db.models import get_models

from nav.util import is_valid_cidr, is_valid_ip
from nav.django import validators, forms as navforms

INFINITY = datetime.max
UNRESOLVED = Q(end_time__gte=INFINITY)


class DateTimeInfinityField(models.DateTimeField):
    def get_db_prep_value(self, value, connection, prepared=False):
        if value == datetime.max:
            value = u'infinity'
        elif value == datetime.min:
            value = u'-infinity'
        else:
            return super(DateTimeInfinityField, self).get_db_prep_value(
                value, connection, prepared=prepared)
        try:
            return connection.ops.value_to_db_datetime(value)  # <= 1.8
        except AttributeError:
            return connection.ops.adapt_datetimefield_value(value)  # >= 1.9


class VarcharField(models.TextField):
    def db_type(self, connection):
        return 'varchar'

    def formfield(self, **kwargs):
        defaults = {
            'widget': forms.TextInput,
        }
        defaults.update(kwargs)
        return super(VarcharField, self).formfield(**defaults)


@six.add_metaclass(models.SubfieldBase)
class DictAsJsonField(models.TextField):
    """Serializes value to and from json. Has a fallback to pickle for
    historical reasons"""

    description = "Field for storing json structure"

    def db_type(self, connection):
        return 'varchar'

    def to_python(self, value):
        if value:
            if isinstance(value, dict):
                return value
            try:
                if isinstance(value, six.binary_type):
                    value = six.text_type(value, encoding='utf-8')
                return json.loads(value)
            except ValueError:
                try:
                    return pickle.loads(value)
                except ValueError:
                    return value
        return {}

    def get_prep_value(self, value):
        if value:
            return json.dumps(value)


@six.add_metaclass(models.SubfieldBase)
class CIDRField(VarcharField):

    def to_python(self, value):
        """Verifies that the value is a string with a valid CIDR IP address"""
        if value:
            if isinstance(value, six.binary_type):
                value = six.text_type(value, encoding='utf-8')
            if not is_valid_cidr(value) and not is_valid_ip(value):
                raise exceptions.ValidationError(
                    "Value must be a valid CIDR address")
        return value


@six.add_metaclass(models.SubfieldBase)
class PointField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 100
        super(PointField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'point'

    def to_python(self, value):
        if not value or isinstance(value, tuple):
            return value
        if isinstance(value, six.string_types):
            if validators.is_valid_point_string(value):
                if value.startswith('(') and value.endswith(')'):
                    noparens = value[1:-1]
                else:
                    noparens = value
                latitude, longitude = noparens.split(',')
                return (Decimal(latitude.strip()), Decimal(longitude.strip()))
        raise exceptions.ValidationError(
            "This value must be a point-string.")

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return None
        if isinstance(value, tuple):
            return '(%s,%s)' % value

    def formfield(self, **kwargs):
        defaults = {'form_class': navforms.PointField}
        defaults.update(kwargs)
        return super(PointField, self).formfield(**defaults)


# this interfaces with Django model protocols, which generates unnecessary
# pylint violations:
# pylint: disable=W0201,W0212
class LegacyGenericForeignKey(object):
    """Generic foreign key for legacy NAV database.

    Some legacy tables in NAV have generic foreign keys that look very much
    like Django's generic foreign keys, except the foreign table name is
    stored directly in the field name.

    """

    def __init__(self, model_name_field, model_fk_field):
        self.mn_field = model_name_field
        self.fk_field = model_fk_field
        if django.VERSION >= (1, 8):
            self.is_relation = True
            self.many_to_many = False
            self.one_to_many = True
            self.related_model = None
            self.auto_created = False

    def contribute_to_class(self, cls, name):
        """Add things to the model class using this descriptor"""
        self.name = name
        self.model = cls
        self.cache_attr = "_%s_cache" % name
        if django.VERSION >= (1, 8):
            cls._meta.virtual_fields.append(self)
        else:
            cls._meta.add_virtual_field(self)

        setattr(cls, name, self)

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        try:
            return getattr(instance, self.cache_attr)
        except AttributeError:
            rel_obj = None

            field = self.model._meta.get_field(self.mn_field)
            table_name = getattr(instance, field.get_attname(), None)
            rel_model = self.get_model_class(table_name)
            if rel_model:
                try:
                    rel_obj = rel_model.objects.get(
                        id=getattr(instance, self.fk_field))
                except exceptions.ObjectDoesNotExist:
                    pass
            setattr(instance, self.cache_attr, rel_obj)
            return rel_obj

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError(
                u"%s must be accessed via instance" % self.name)

        table_name = None
        fkey = None
        if value is not None:
            table_name = value._meta.db_table
            fkey = value._get_pk_val()

        setattr(instance, self.mn_field, table_name)
        setattr(instance, self.fk_field, fkey)
        setattr(instance, self.cache_attr, value)

    @staticmethod
    def get_model_class(table_name):
        """Returns a Model class based on a database table name"""
        classmap = dict((m._meta.db_table, m) for m in get_models())
        if table_name in classmap:
            return classmap[table_name]

# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Uninett AS
# Copyright (C) 2022 Sikt
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
from typing import Optional

from django import forms
from django.db import models
from django.db.models import signals
from django.db.models.fields.mixins import FieldCacheMixin
from django.core import exceptions
from django.db.models import Q
from django.apps import apps

from nav.util import is_valid_cidr, is_valid_ip
from nav.django import validators, forms as navforms

INFINITY = datetime.max
UNRESOLVED = Q(end_time__gte=INFINITY)


class DateTimeInfinityField(models.DateTimeField):
    def get_db_prep_value(self, value, connection, prepared=False):
        if value == datetime.max:
            value = 'infinity'
        elif value == datetime.min:
            value = '-infinity'
        else:
            return super(DateTimeInfinityField, self).get_db_prep_value(
                value, connection, prepared=prepared
            )
        return connection.ops.adapt_datetimefield_value(value)


class VarcharField(models.TextField):
    def db_type(self, connection):
        return 'varchar'

    def formfield(self, **kwargs):
        defaults = {
            'widget': forms.TextInput,
        }
        defaults.update(kwargs)
        return super(VarcharField, self).formfield(**defaults)


class DictAsJsonField(models.TextField):
    """Serializes value to and from json. Has a fallback to pickle for
    historical reasons"""

    description = "Field for storing json structure"

    def db_type(self, connection):
        return 'varchar'

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value:
            if isinstance(value, dict):
                return value
            try:
                # Needs str
                return json.loads(
                    str(value, encoding="utf-8") if isinstance(value, bytes) else value
                )
            except ValueError:
                try:
                    # Needs bytes
                    return pickle.loads(
                        bytes(value, encoding="utf-8")
                        if isinstance(value, str)
                        else value
                    )
                except ValueError:
                    return value
        return {}

    def get_prep_value(self, value):
        if value:
            return json.dumps(value)


class CIDRField(VarcharField):
    def to_python(self, value):
        """Verifies that the value is a string with a valid CIDR IP address"""
        if value:
            if isinstance(value, bytes):
                value = str(value, encoding='utf-8')
            if not is_valid_cidr(value) and not is_valid_ip(value):
                raise exceptions.ValidationError("Value must be a valid CIDR address")
        return value


class PointField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 100
        super(PointField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'point'

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if not value or isinstance(value, tuple):
            return value
        if isinstance(value, str) and validators.is_valid_point_string(value):
            noparens = value.removeprefix("(").removesuffix(")")
            latitude, longitude = noparens.split(',')
            return (Decimal(latitude.strip()), Decimal(longitude.strip()))
        raise exceptions.ValidationError("This value must be a point-string.")

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return None
        if isinstance(value, tuple):
            return '(%s,%s)' % value

    def formfield(self, **kwargs):
        defaults = {'form_class': navforms.PointField}
        defaults.update(kwargs)
        return super(PointField, self).formfield(**defaults)


class LegacyGenericForeignKey(FieldCacheMixin):
    """Generic foreign key for legacy NAV database.

    Some legacy tables in NAV have generic foreign keys that look very much
    like Django's generic foreign keys, except the foreign table name is
    stored directly in the field name.

    """

    # Field flags
    auto_created = False
    concrete = False
    editable = False
    hidden = False

    is_relation = True
    many_to_many = False
    many_to_one = True
    one_to_one = False
    related_model = None
    remote_field = None

    def __init__(self, model_name_field, model_fk_field, for_concrete_model=True):
        self.mn_field = model_name_field
        self.fk_field = model_fk_field
        self.one_to_many = True
        self.editable = False
        self.for_concrete_model = for_concrete_model

    def __str__(self):
        modelname = getattr(self, 'mn_field')
        fk = getattr(self, 'fk_field')
        return '{}={}'.format(modelname, fk)

    def contribute_to_class(self, cls, name):
        """Add things to the model class using this descriptor"""
        self.name = name
        self.model = cls
        cls._meta.private_fields.append(self)

        if not cls._meta.abstract:
            signals.pre_init.connect(self.instance_pre_init, sender=cls)

        setattr(cls, name, self)

    def get_cache_name(self):
        return self.name

    def instance_pre_init(self, signal, sender, args, kwargs, **_kwargs):
        """
        Handles initializing an object with the generic FK instead of
        content-type/object-id fields.
        """
        if self.name in kwargs:
            value = kwargs.pop(self.name)
            if value is not None:
                kwargs[self.mn_field] = self.get_model_name(value)
                kwargs[self.fk_field] = value._get_pk_val()
            else:
                kwargs[self.mn_field] = None
                kwargs[self.fk_field] = None

    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        rel_obj = self.get_cached_value(instance, default=None)

        field = self.model._meta.get_field(self.mn_field)
        table_name = getattr(instance, field.get_attname(), None)
        rel_model = self.get_model_class(table_name)
        if rel_model:
            try:
                rel_obj = rel_model.objects.get(id=getattr(instance, self.fk_field))
            except exceptions.ObjectDoesNotExist:
                pass
        self.set_cached_value(instance, rel_obj)
        return rel_obj

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("%s must be accessed via instance" % self.name)

        table_name = None
        fkey = None
        if value is not None:
            table_name = self.get_model_name(value)
            fkey = value._get_pk_val()

        setattr(instance, self.mn_field, table_name)
        setattr(instance, self.fk_field, fkey)
        self.set_cached_value(instance, value)

    @staticmethod
    def get_model_name(obj) -> str:
        return obj._meta.db_table

    @staticmethod
    def get_model_class(table_name) -> Optional[models.Model]:
        """Returns a Model class based on a database table name"""
        classmap = {model._meta.db_table: model for model in apps.get_models()}
        if table_name in classmap:
            return classmap[table_name]

# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Storage layer for ipdevpoll"""

import logging

import django.db.models

from nav.models import manage
from nav import ipdevpoll

# dict structure: { django_model_class: shadow_class }
shadowed_classes = {}


class MetaShadow(type):
    """Metaclass for building storage container classes.

    A shadow class built by this metaclass will look mostly like its
    Django model counterpart, but will be a dumb container.  Usage of
    attributes in such a container will guarantee that no database
    access occurs, and should therefore not introduce unwanted delays
    inside an asynchronous event loop.

    """

    def __init__(cls, name, bases, dct):
        try:
            shadowclass = dct['__shadowclass__']
        except KeyError, error:
            raise AttributeError("No shadow attribute in class %s" % name)

        super(MetaShadow, cls).__init__(name, bases, dct)
        
        if shadowclass is None:
            return

        field_names = [f.name for f in shadowclass._meta.fields]
        setattr(cls, '_fields', field_names)
        for f in field_names:
            setattr(cls, f, None)

        shadowed_classes[shadowclass] = cls

class Shadow(object):
    """Base class to shadow Django model classes.

    To create a "dumb" container of values, whose attribute list will
    be equal to that of a Django model class, define a descendant of
    this class and set its __shadowclass__ attribute to the Django
    model class.

    Using shadow containers will ensure no synchronous database calls
    take place behind the scenes.

    Example:

    >>> from nav.models import manage
    >>> class Netbox(Shadow):
    ...     __shadowclass__ = manage.Netbox
    ...
    >>>

    """
    __shadowclass__ = None
    __metaclass__ = MetaShadow
    __lookups__ = []

    def __init__(self, *args, **kwargs):
        """Initialize a shadow container.

        To copy the values of a Django model object, supply the object
        as the first argument.  Any keyword arguments will be used to
        initialize the attributes of the container object.

        If an object of a shadowed class is assigned as an attribute's
        value, the attribute will be changed into a shadowed object.
        This is to ensure no live Django model objects will live
        inside the object hierarchy.

        """
        self._logger = ipdevpoll.get_class_logger(self.__class__)
        if args:
            obj = args[0]
            if isinstance(obj, self.__class__.__shadowclass__):
                for field in self.__class__._fields:
                    setattr(self, field, getattr(obj, field))
            else:
                raise ValueError("First argument is not a %s instance" %
                                 self.__class__.__shadowclass__.__name__)
        else:
            for key, val in kwargs.items():
                if not hasattr(self.__class__, key):
                    raise AttributeError("Invalid keyword argument %s" % key)
                setattr(self, key, val)

        self._touched = set()

    def __repr__(self):
        attrs = [field for field in self._fields
                 if getattr(self, field) is not None or 
                 field in self._touched]
        varbinds = ["%s=%r" % (field, getattr(self, field))
                    for field in attrs]
        return "%s(%s)" % (self.__class__.__name__, ", ".join(varbinds))

    def __setattr__(self, attr, value):
        """Set attribute and register it as having been touched.

        See the get_touched() method for more info.

        """
        # The _touched attribute will not exist during initialization
        # of the object, so ignore AttributeErrors
        try:
            self._touched.add(attr)
        except AttributeError:
            pass

        # If the passed value belongs to a shadowed class, replace it
        # with a shadow object.
        if value.__class__ in shadowed_classes:
            shadow = shadowed_classes[value.__class__]
            value = shadow(value)
        else:
            if isinstance(value, django.db.models.Model):
                self._logger.warning(
                    "Live model object being added to %r attribute: %r",
                    value, attr)
        return super(Shadow, self).__setattr__(attr, value)

    def get_touched(self):
        """Get list of touched attributes.

        Returns a list of attributes that have been modified since
        this container's creation.

        """
        return list(self._touched)

    def get_model(self):
        """Return a live Django model object based on the data of this one.
        
        If this shadow object represents something that is already in
        the database, the existing database object will be retrieved
        synchronously, and its attributes modified with the contents
        of the touched attributes of the shadow object.

        """
        # Get existing or create new instance
        model = self.get_existing_model() or self.__shadowclass__()

        # Copy all modified attributes to the empty model object
        for attr in self._touched:
            # FIXME Must have some intelligence here.  If the value is
            # a shadowed object, this too must be transformed into a
            # model object.
            value = getattr(self, attr)
            setattr(model, attr, value)
        return model

    def get_existing_model(self):
        """Return an existing live Django model object.

        If the object represented by this shadow already exists in the
        database, this method will return it from the database.  If
        such an object doesn't exist, the None value will be returned.

        TODO:  Allow multi-field lookups (fields listed in a tuple)
        """
        # Find out which attribute is the primary key, add it to the
        # list of lookup fields
        pk_attr = self.__shadowclass__._meta.pk.name
        lookups = [pk_attr] + self.__lookups__
        
        # Try each lookup field and see which one corresponds to
        # something in the a database, if any
        for lookup in lookups:
            value = getattr(self, lookup)
            if value is not None:
                kwargs = {lookup: value}
                try:
                    model = self.__shadowclass__.objects.get(**kwargs)
                except self.__shadowclass__.DoesNotExist, e:
                    pass
                else:
                    return model


def shadowify(model):
    """Return a properly shadowed version of a Django model object.

    If no shadow class exists for the object's class, the original
    object is returned as-is.

    """
    cls = model.__class__
    if cls in shadowed_classes:
        new_cls = shadowed_classes[cls]
        model = new_cls(model)
    return model

def shadowify_queryset(queryset):
    """Run a Django queryset and transform results to shadow containers."""
    result = list(queryset)
    new_list = [shadowify(obj) for obj in result]
    return new_list


# Shadow classes.  Not all of these will be used to store data, but
# may be used to retrieve and cache existing database records.

class Netbox(Shadow):
    __shadowclass__ = manage.Netbox
    __lookups__ = ['sysname', 'ip']

class NetboxType(Shadow):
    __shadowclass__ = manage.NetboxType

class Vendor(Shadow):
    __shadowclass__ = manage.Vendor

class Module(Shadow):
    __shadowclass__ = manage.Module

class Device(Shadow):
    __shadowclass__ = manage.Device

class Interface(Shadow):
    __shadowclass__ = manage.Interface

class Location(Shadow):
    __shadowclass__ = manage.Location

class Room(Shadow):
    __shadowclass__ = manage.Room

class Category(Shadow):
    __shadowclass__ = manage.Category

class Organization(Shadow):
    __shadowclass__ = manage.Organization

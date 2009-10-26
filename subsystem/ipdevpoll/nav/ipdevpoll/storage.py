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
        self.delete = False
        self.update_only = False

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if not self.__shadowclass__ == other.__shadowclass__:
            return False

        for lookup in self.__lookups__:
            if isinstance(lookup, tuple):
                ret = True
                for field in lookup:
                    try:
                        if getattr(self, field) != getattr(other, field):
                            ret = False
                    except AttributeError:
                        ret = False
                if ret:
                    return ret
            else:
                try:
                    if getattr(self, lookup) == getattr(other, lookup):
                        return True
                except AttributeError:
                    continue
        return False

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

    @classmethod
    def get_dependencies(cls):
        """Get a list of other shadow classes this class depends on.

        Returns:

          A list of shadow classes that are known to be foreign keys
          on this one.

        """
        dependencies = []
        django_model = cls.__shadowclass__
        for field in django_model._meta.fields:
            if issubclass(field.__class__, 
                          django.db.models.fields.related.ForeignKey):
                django_dependency = field.rel.to

                if django_dependency in shadowed_classes:
                    shadow_dependency = shadowed_classes[django_dependency]
                    dependencies.append(shadow_dependency)
        return dependencies

    def get_touched(self):
        """Get list of touched attributes.

        Returns a list of attributes that have been modified since
        this container's creation.

        """
        return list(self._touched)

    def convert_to_model(self, containers=None):
        """Return a live Django model object based on the data of this one.

        If this shadow object represents something that is already in
        the database, the existing database object will be retrieved
        synchronously, and its attributes modified with the contents
        of the touched attributes of the shadow object.

        The current job handler's containers are provided for asvanced lookups
        overrides in certain shadow classes. The containers argument is a dictionary
        with keyed by the shadowclass. The value connected to the key is a dictionary
        with shadow instances keyed by their index created upon container creation.
        """

        if not container_list:
            container_list = {}

        # Get existing or create new instance
        model = self.get_existing_model(containers)
        if not model and self.update_only:
            return None
        elif not model:
            model = self.__shadowclass__()

        # Copy all modified attributes to the empty model object
        for attr in self._touched:
            value = getattr(self, attr)
            if issubclass(value.__class__, Shadow):
                value = value.get_model()
            setattr(model, attr, value)
        return model

    def get_primary_key_attribute(self):
        """Return a reference to the corresponding Django model's primary key
        attribute.
        """
        return self.__shadowclass__._meta.pk

    def get_primary_key(self):
        """Return the value of the primary key, if set."""
        pk = self.get_primary_key_attribute()
        return getattr(self, pk.name)

    def set_primary_key(self, value):
        """Set the value of the primary key."""
        pk = self.get_primary_key_attribute()
        setattr(self, pk.name, value)

    def get_existing_model(self):
        """Return an existing live Django model object.

        If the object represented by this shadow already exists in the
        database, this method will return it from the database.  If
        such an object doesn't exist, the None value will be returned.
        """
        # Find the primary key attribute.  If the primary key is also
        # a foreign key, we need to get the existing model for the
        # foreign key first.  Either way, the primary key attribute
        # name is added to the list of lookup fields.
        pk = self.get_primary_key_attribute()
        pk_value = self.get_primary_key()
        lookups = [pk.name] + self.__lookups__

        if issubclass(pk_value.__class__, Shadow):
            pk_value = pk_value.get_existing_model()

        # If we have the primary key, we can return almost at once
        # If PK is AutoField, we raise an exception if the object
        # does not exist.
        if pk_value:
            try:
                model = self.__shadowclass__.objects.get(pk=pk_value)
            except self.__shadowclass__.DoesNotExist, e:
                if self.__shadowclass__._meta.pk.__class__ == django.db.models.fields.AutoField:
                    raise e
                else:
                    return None
            return model

        # Try each lookup field and see which one corresponds to
        # something in the a database, if any
        for lookup in lookups:
            kwargs = None
            if isinstance(lookup, tuple):
                kwargs = dict(zip(lookup, map(lambda l: getattr(self, l), lookup)))
            else:
                value = getattr(self, lookup)
                if value is not None:
                    kwargs = {lookup: value}
            if kwargs:
                # Ensure we only have django models
                for key, val in kwargs.items():
                    if issubclass(val.__class__, Shadow):
                        kwargs[key] = val.get_model()
                try:
                    model = self.__shadowclass__.objects.get(**kwargs)
                except self.__shadowclass__.DoesNotExist, e:
                    pass
                else:
                    # Set our primary key from the existing object in an
                    # attempt to achieve consistency
                    setattr(self, pk.name, model.pk)
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



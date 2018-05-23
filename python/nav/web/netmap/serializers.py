#
# Copyright (C) 2014 Uninett AS
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
"""Serializer classes for netmap"""
from django.forms.widgets import SelectMultiple, Textarea
from django.shortcuts import get_object_or_404
from django.utils.six import iteritems

from rest_framework import serializers

from nav.models import profiles
from nav.models.manage import Category


class MultipleChoiceField(serializers.ChoiceField):
    """A generic multiple choice field

        This does not currently exist in django-rest-framework
    """
    widget = SelectMultiple

    def field_from_native(self, data, files, field_name, into):
        if type(data) is dict:
            into[field_name] = data.get(field_name, [])
        else:
            # If using django rest frameworks api browser
            # `data` will be a django QueryDict object
            # If the api browser is not to be used, this
            # clause is unnecessary an can be removed
            into[field_name] = dict(data.iterlists()).get(field_name, [])


class InstanceRelatedField(serializers.RelatedField):
    """A field to deserialize foreign keys to instances"""

    def __init__(self, related_class=None, *args, **kwargs):
        self.related_class = related_class
        super(InstanceRelatedField, self).__init__(args, kwargs)

    def from_native(self, value):
        if self.related_class is not None:
            return get_object_or_404(self.related_class, pk=value)

        return super(InstanceRelatedField, self).from_native(value)


class NetmapViewSerializer(serializers.Serializer):
    """Serializer for NetmapView"""
    viewid = serializers.Field()
    owner = serializers.RelatedField(read_only=True)
    title = serializers.CharField()
    description = serializers.CharField(required=False)
    topology = serializers.ChoiceField(choices=profiles.LINK_TYPES)
    zoom = serializers.CharField(required=False)
    last_modified = serializers.DateTimeField()
    is_public = serializers.BooleanField()
    # Cannot set choices to actual data here, breaks import of models
    categories = serializers.MultipleChoiceField([])
    location_room_filter = serializers.CharField(max_length=255, required=False)
    display_orphans = serializers.BooleanField()
    display_elinks = serializers.BooleanField()

    def __init__(self, *args, **kwargs):
        super(NetmapViewSerializer, self).__init__(*args, **kwargs)
        self.fields['categories'].choices = [
            (category, category)
            for category in Category.objects.values_list('id', flat=True)
        ]

    def restore_object(self, attrs, instance=None):

        if instance is not None:

            for key, value in iteritems(attrs):
                setattr(instance, key, value)
            return instance

        categories = attrs.pop('categories')
        instance = profiles.NetmapView(**attrs)
        setattr(instance, 'categories', categories)
        return instance

    def to_native(self, obj):
        if obj:
            categories = [
                view_category.category.id
                for view_category in obj.categories_set.all().select_related(
                    'category'
                )
            ]
            setattr(obj, 'categories', categories)
        return super(NetmapViewSerializer, self).to_native(obj)


class NetmapViewDefaultViewSerializer(serializers.ModelSerializer):
    """Serializer for NetmapViewDefault"""
    partial = True

    class Meta(object):
        model = profiles.NetmapViewDefaultView

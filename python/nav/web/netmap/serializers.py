#
# Copyright (C) 2014 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Serializer classes for netmap"""

from django.forms.widgets import SelectMultiple
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from nav.models import profiles, manage


class MultipleChoiceField(serializers.ChoiceField):
    """A generic multiple choice field

    This does not currently exist in django-rest-framework
    """

    widget = SelectMultiple

    def field_from_native(self, data, files, field_name, into):
        if isinstance(data, dict):
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


class SimpleCategorySerializer(serializers.ModelSerializer):
    """Simple serializer to represent categories as strings based on their PK"""

    class Meta:
        model = manage.Category
        fields = ('id',)

    def to_representation(self, instance):
        return instance.pk

    @staticmethod
    def to_internal_value(data):
        return manage.Category.objects.get(pk=data)


class NetmapViewSerializer(serializers.Serializer):
    """Serializer for NetmapView"""

    viewid = serializers.IntegerField(required=False, read_only=True)
    owner = serializers.StringRelatedField(read_only=True)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    topology = serializers.ChoiceField(choices=profiles.LINK_TYPES)
    zoom = serializers.CharField(required=False)
    last_modified = serializers.DateTimeField()
    is_public = serializers.BooleanField()
    categories = SimpleCategorySerializer(many=True)
    location_room_filter = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )
    display_orphans = serializers.BooleanField()
    display_elinks = serializers.BooleanField()

    def update(self, instance, validated_data):
        new_categories = set(validated_data.pop('categories'))

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        self._update_categories(instance, new_categories)
        return instance

    def create(self, validated_data):
        categories = set(validated_data.pop('categories'))
        instance = profiles.NetmapView(**validated_data)
        instance.save()

        self._update_categories(instance, categories)

        return instance

    @staticmethod
    def _update_categories(instance, new_categories):
        old_categories = set(instance.categories.all())
        add_categories = new_categories - old_categories
        del_categories = old_categories - new_categories

        # Delete removed categories
        instance.netmap_view_categories.filter(category__in=del_categories).delete()

        # Create added categories
        profiles.NetmapViewCategories.objects.bulk_create(
            [
                profiles.NetmapViewCategories(view=instance, category=cat)
                for cat in add_categories
            ]
        )


class NetmapViewDefaultViewSerializer(serializers.ModelSerializer):
    """Serializer for NetmapViewDefault"""

    partial = True

    class Meta(object):
        model = profiles.NetmapViewDefaultView
        fields = ('view',)

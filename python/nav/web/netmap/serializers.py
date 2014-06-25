from django.forms.widgets import SelectMultiple, Textarea
from django.shortcuts import get_object_or_404

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

    viewid = serializers.Field()
    owner = serializers.RelatedField()
    title = serializers.CharField(widget=Textarea)
    description = serializers.CharField(widget=Textarea)
    topology = serializers.ChoiceField(choices=profiles.LINK_TYPES)
    zoom = serializers.CharField(required=False)
    last_modified = serializers.DateTimeField()
    is_public = serializers.BooleanField()
    categories = MultipleChoiceField(
        choices=[
            (category, category)
            for category in Category.objects.values_list('id', flat=True)
        ],
    )
    display_orphans = serializers.BooleanField()
    display_elinks = serializers.BooleanField()

    def restore_object(self, attrs, instance=None):

        if instance is not None:

            for key, value in attrs.iteritems():
                setattr(instance, key, value)
            return instance

        categories = attrs.pop('categories')
        instance = profiles.NetmapView(**attrs)
        setattr(instance, 'categories', categories)
        return instance

    def to_native(self, obj):
        if obj is not None:
            categories = [
                view_category.category.id
                for view_category in obj.categories_set.all().select_related(
                    'category'
                )
            ]
            setattr(obj, 'categories', categories)
        return super(NetmapViewSerializer, self).to_native(obj)


class NetmapViewDefaultViewSerializer(serializers.ModelSerializer):
    partial = True

    class Meta:
        model = profiles.NetmapViewDefaultView
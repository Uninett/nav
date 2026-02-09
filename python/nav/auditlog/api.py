# Copyright (C) 2017 Uninett AS
# Copyright (C) 2022 Sikt
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

from django.db.models import Q

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, serializers, viewsets
from rest_framework.response import Response

from nav.models.fields import LegacyGenericForeignKey
from nav.web.api.v1.views import NAVAPIMixin

from nav.models.manage import Interface

from .models import LogEntry

ENTITY_FIELDS = (
    ('actor_model', 'actor_pk'),
    ('object_model', 'object_pk'),
    ('target_model', 'target_pk'),
)


def _collect_entity_references(entries):
    """Collect all (model_name, pk) pairs from a page of log entries,
    grouped by model name for batch fetching."""
    lookups = {}
    for entry in entries:
        for model_field, pk_field in ENTITY_FIELDS:
            model_name = getattr(entry, model_field)
            pk = getattr(entry, pk_field)
            if model_name and pk:
                lookups.setdefault(model_name, set()).add(pk)
    return lookups


def _batch_resolve_objects(entries):
    """Batch-resolve referenced objects for a page of log entries.

    Returns a dict of (model_name, pk) -> {'name': str, 'url': str|None}
    with one query per distinct model type instead of one per entity.
    """
    references = _collect_entity_references(entries)
    resolved = {}
    for model_name, pks in references.items():
        rel_model = LegacyGenericForeignKey.get_model_class(model_name)
        if not rel_model:
            continue
        try:
            for obj in rel_model.objects.filter(id__in=pks):
                url = getattr(obj, 'get_absolute_url', lambda: None)()
                resolved[(model_name, str(obj.pk))] = {
                    'name': str(obj),
                    'url': url,
                }
        except (TypeError, ValueError):
            pass

    return resolved


def _resolve_entity(log_entry, model_field, pk_field, sortkey_field, object_cache):
    """Resolve a LGFK entity to {name, url}.

    Prefers the live object name from the object_cache (built by
    _batch_resolve_objects), falling back to the stored sortkey for deleted
    objects, and finally to a raw "model (pk)" label.
    """
    model_name = getattr(log_entry, model_field)
    pk = getattr(log_entry, pk_field)

    if not model_name or not pk:
        return None

    sortkey = getattr(log_entry, sortkey_field)
    cached = object_cache.get((model_name, pk))

    if cached:
        name = cached['name']
    elif sortkey:
        name = sortkey
    else:
        name = '{} ({})'.format(model_name, pk)
    url = cached['url'] if cached else None

    return {'name': name, 'url': url}


class LogEntrySerializer(serializers.ModelSerializer):
    """V1 serializer - returns plain strings for backward compatibility"""

    actor = serializers.CharField(source='actor_sortkey')
    object = serializers.CharField(source='object_sortkey')
    target = serializers.CharField(source='target_sortkey')

    class Meta:
        model = LogEntry
        fields = [
            'timestamp',
            'subsystem',
            'actor',
            'verb',
            'object',
            'target',
            'summary',
            'before',
            'after',
        ]
        read_only_fields = ['timestamp']


class LogEntrySerializerV2(serializers.ModelSerializer):
    """V2 serializer - returns objects with {name, url} for entity linking"""

    actor = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = LogEntry
        fields = [
            'timestamp',
            'subsystem',
            'actor',
            'verb',
            'object',
            'target',
            'summary',
            'before',
            'after',
        ]
        read_only_fields = ['timestamp']

    @property
    def _object_cache(self):
        return self.context.get('object_cache', {})

    def get_actor(self, obj):
        return _resolve_entity(
            obj, 'actor_model', 'actor_pk', 'actor_sortkey', self._object_cache
        )

    def get_object(self, obj):
        return _resolve_entity(
            obj, 'object_model', 'object_pk', 'object_sortkey', self._object_cache
        )

    def get_target(self, obj):
        return _resolve_entity(
            obj, 'target_model', 'target_pk', 'target_sortkey', self._object_cache
        )


class MultipleFilter(filters.BaseFilterBackend):
    """Allows filtering on multiples

    object_pks: comma-separated list of pks to filter on
    object_model: supports multiple object_models
    """

    def filter_queryset(self, request, queryset, view):
        if 'object_pks' in request.query_params:
            ids = request.query_params.get('object_pks').split(',')
            queryset = queryset.filter(object_pk__in=ids)
        if 'object_model' in request.query_params:
            queryset = queryset.filter(
                object_model__in=request.query_params.getlist('object_model')
            )
        return queryset


class NetboxFilter(filters.BaseFilterBackend):
    """Filters all log entries for a netbox

    This includes all entries where the object_model is 'netbox' and all
    entries where the object_model is 'interface' and the netbox of the
    interface is this netbox
    """

    def filter_queryset(self, request, queryset, view):
        if 'netboxid' in request.query_params:
            netboxid = request.query_params.get('netboxid')
            interface_pks = [
                str(pk)
                for pk in Interface.objects.filter(netbox__pk=netboxid).values_list(
                    'pk', flat=True
                )
            ]

            is_netbox = Q(object_model='netbox', object_pk=netboxid)
            is_netbox_interface = Q(
                object_model='interface', object_pk__in=interface_pks
            )
            queryset = queryset.filter(is_netbox | is_netbox_interface)

        return queryset


class NAVDefaultsMixin(object):
    authentication_classes = NAVAPIMixin.authentication_classes
    permission_classes = NAVAPIMixin.permission_classes
    renderer_classes = NAVAPIMixin.renderer_classes
    filter_backends = NAVAPIMixin.filter_backends


class LogEntryViewSet(NAVDefaultsMixin, viewsets.ReadOnlyModelViewSet):
    """V1 API endpoint - returns plain strings for backward compatibility.

    Logentries are created behind the scenes by the subsystems themselves."""

    filter_backends = (
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter,
        MultipleFilter,
        NetboxFilter,
    )
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    filterset_fields = ('subsystem', 'object_pk', 'verb')
    search_fields = ('summary', 'actor_sortkey', 'object_sortkey', 'target_sortkey')
    ordering = ('timestamp',)
    ordering_fields = (
        'timestamp',
        'actor_sortkey',
        'verb',
        'object_sortkey',
        'target_sortkey',
    )


class LogEntryViewSetV2(NAVDefaultsMixin, viewsets.ReadOnlyModelViewSet):
    """V2 API endpoint - returns objects with {name, url} for entity linking.

    Logentries are created behind the scenes by the subsystems themselves."""

    filter_backends = (
        filters.SearchFilter,
        DjangoFilterBackend,
        filters.OrderingFilter,
        MultipleFilter,
        NetboxFilter,
    )
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializerV2
    filterset_fields = ('subsystem', 'object_pk', 'verb')
    search_fields = ('summary', 'actor_sortkey', 'object_sortkey', 'target_sortkey')
    ordering = ('timestamp',)
    ordering_fields = (
        'timestamp',
        'actor_sortkey',
        'verb',
        'object_sortkey',
        'target_sortkey',
    )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        entries = page if page is not None else list(queryset)
        object_cache = _batch_resolve_objects(entries)
        context = {**self.get_serializer_context(), 'object_cache': object_cache}
        serializer = self.get_serializer(entries, many=True, context=context)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        object_cache = _batch_resolve_objects([instance])
        context = {**self.get_serializer_context(), 'object_cache': object_cache}
        serializer = self.get_serializer(instance, context=context)
        return Response(serializer.data)

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

import operator

from django.db.models import Q
import six

from rest_framework import serializers
from rest_framework import viewsets, filters

from nav.web.api.v1.views import NAVAPIMixin

from nav.models.manage import Interface

from .models import LogEntry


class LGFKRelatedField(serializers.RelatedField):
    """
    Custom field for any LegacyGenericForeignKey
    """

    def to_representation(self, value):
        return six.text_type(value)


class LogEntrySerializer(serializers.ModelSerializer):
    actor = LGFKRelatedField(read_only=True)
    object = LGFKRelatedField(read_only=True)
    target = LGFKRelatedField(read_only=True)

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


class CustomOrderingFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        """Order by actor login

        Sad things happen if the actor is not an account
        """
        ordering = request.query_params.get('ordering')
        if ordering in ['-actor', 'actor']:
            return sorted(
                queryset,
                key=operator.attrgetter('actor.login'),
                reverse=ordering.startswith('-'),
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
    """Read only api endpoint for logentries.

    Logentries are created behind the scenes by the subsystems themselves."""

    filter_backends = NAVDefaultsMixin.filter_backends + (
        MultipleFilter,
        CustomOrderingFilter,
        NetboxFilter,
    )
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    filterset_fields = ('subsystem', 'object_pk', 'verb')
    search_fields = ('summary',)
    ordering = ('timestamp',)

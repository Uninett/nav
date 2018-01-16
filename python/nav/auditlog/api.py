# Copyright (C) 2017 UNINETT AS
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

from rest_framework import serializers
from rest_framework import viewsets, filters

from nav.web.api.v1.views import NAVAPIMixin

from .models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField('get_actor')
    object = serializers.SerializerMethodField('get_object')
    target = serializers.SerializerMethodField('get_target')

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

    def get_actor(self, obj):
        return obj.actor

    def get_object(self, obj):
        return obj.object

    def get_target(self, obj):
        return obj.target


class MultipleFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if 'object_pk[]' in request.QUERY_PARAMS:
            ids = request.QUERY_PARAMS.getlist('object_pk[]')
            queryset = queryset.filter(object_pk__in=ids)
        return queryset


class NAVDefaultsMixin(object):
    authentication_classes = NAVAPIMixin.authentication_classes
    permission_classes = NAVAPIMixin.permission_classes
    renderer_classes = NAVAPIMixin.renderer_classes
    filter_backends = NAVAPIMixin.filter_backends


class LogEntryViewSet(NAVDefaultsMixin, viewsets.ReadOnlyModelViewSet):
    """Read only api endpoint for logentries.

    Logentries are created behind the scenes by the subsystems themselves."""

    filter_backends = NAVDefaultsMixin.filter_backends + (MultipleFilter, )
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    filter_fields = ('subsystem', 'object_pk', 'object_model')

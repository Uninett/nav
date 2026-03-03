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

from django.db.models import Case, F, IntegerField, OuterRef, Q, Subquery, When
from django.db.models.functions import Cast

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, serializers, viewsets

from nav.web.api.v1.views import NAVAPIMixin

from nav.models.manage import Interface
from nav.models.profiles import Account

from .models import LogEntry


class LGFKRelatedField(serializers.RelatedField):
    """
    Custom field for any LegacyGenericForeignKey
    """

    def to_representation(self, value):
        return str(value)


class LogEntrySerializer(serializers.ModelSerializer):
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

    def get_actor(self, instance):
        if instance.actor:
            return str(instance.actor)
        if instance.actor_model:
            return f"{instance.actor_model} deleted"
        return None

    def get_object(self, instance):
        if instance.object:
            return str(instance.object)
        if instance.object_model:
            return f"{instance.object_model} deleted"
        return None

    def get_target(self, instance):
        if instance.target:
            return str(instance.target)
        if instance.target_model:
            return f"{instance.target_model} deleted"
        return None


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


class LogEntryOrderingFilter(filters.OrderingFilter):
    """Custom ordering filter that handles the 'actor' field specially.

    The 'actor' field is a LegacyGenericForeignKey and cannot be used with
    Django's queryset order_by(). Instead, we use a subquery to fetch the
    actor's login from the Account table for efficient database-level sorting.
    """

    def filter_queryset(self, request, queryset, view):
        ordering = request.query_params.get('ordering')
        if ordering in ['-actor', 'actor']:
            actor_login = Case(
                When(
                    actor_pk__regex=r'^\d+$',
                    then=Subquery(
                        Account.objects.filter(
                            id=Cast(OuterRef('actor_pk'), IntegerField())
                        ).values('login')[:1]
                    ),
                ),
                default=F('actor_pk'),
            )
            queryset = queryset.annotate(actor_login=actor_login)
            if ordering == '-actor':
                return queryset.order_by(F('actor_login').desc(nulls_last=True))
            return queryset.order_by(F('actor_login').asc(nulls_last=True))
        return super().filter_queryset(request, queryset, view)


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

    filter_backends = (
        filters.SearchFilter,
        DjangoFilterBackend,
        LogEntryOrderingFilter,
        MultipleFilter,
        NetboxFilter,
    )
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer
    filterset_fields = ('subsystem', 'object_pk', 'verb')
    search_fields = ('summary',)
    ordering = ('timestamp',)

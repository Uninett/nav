# Copyright (C) 2013 Uninett AS
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
#
"""Views for the NAV API"""

from datetime import datetime, timedelta
import logging
from typing import Sequence

from IPy import IP
from django.http import HttpResponse, JsonResponse, QueryDict
from django.db.models import Q
from django.db.models.fields.related import ManyToOneRel as _RelatedObject
from django.core.exceptions import FieldDoesNotExist
import django.db
import iso8601
import json

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters.filters import ModelMultipleChoiceFilter, CharFilter
from rest_framework import status, filters, viewsets, exceptions
from rest_framework.decorators import api_view, renderer_classes, action
from rest_framework.reverse import reverse_lazy
from rest_framework.renderers import (
    JSONRenderer,
    BrowsableAPIRenderer,
    TemplateHTMLRenderer,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.serializers import ValidationError

from oidc_auth.authentication import JSONWebTokenAuthentication
import jwt

from nav.django.settings import JWT_PUBLIC_KEY, JWT_NAME, LOCAL_JWT_IS_CONFIGURED
from nav.macaddress import MacAddress
from nav.models import manage, event, cabling, rack, profiles
from nav.models.api import JWTRefreshToken
from nav.models.fields import INFINITY, UNRESOLVED
from nav.web.auth.utils import get_account
from nav.web.servicecheckers import load_checker_classes
from nav.util import auth_token, is_valid_cidr

from nav.buildconf import VERSION
from nav.web.api.v1 import serializers, alert_serializers
from nav.web.status2 import STATELESS_THRESHOLD
from nav.web.jwtgen import (
    decode_token,
    generate_access_token,
    generate_refresh_token,
    hash_token,
)
from nav.macaddress import MacPrefix
from .auth import (
    APIAuthentication,
    DefaultPermission,
    NavBaseAuthentication,
    RelaxedReadPermission,
)
from .helpers import prefix_collector
from .filter_backends import (
    AlertHistoryFilterBackend,
    IfClassFilter,
    NaturalIfnameFilter,
    NetboxIsOnMaintenanceFilterBackend,
)

EXPIRE_DELTA = timedelta(days=365)
MINIMUMPREFIXLENGTH = 4
_logger = logging.getLogger(__name__)


class Iso8601ParseError(exceptions.ParseError):
    default_detail = (
        'Wrong format on timestamp. See https://pypi.python.org/pypi/iso8601'
    )


class IPParseError(exceptions.ParseError):
    default_detail = (
        'ip field must be a valid IPv4 or IPv6 host address or network prefix'
    )


@api_view(('GET',))
@renderer_classes((JSONRenderer, BrowsableAPIRenderer))
def api_root(request):
    """
    Some endpoints support write operations. They have a POST in the
    Allow-header.

    To get programmatic access to the API you need a token. Read more
    in the official [documentation][1].

    Paging
    ------
    `/api/netbox/?page_size=10`

    Default page_size is 100

    Searching
    ---------
    `/api/netbox/?search=something`

    Which fields are searched is documented for each endpoint.

    Filtering
    ---------
    `/api/netbox/?category=GSW`

    Which fields can be used for filtering is documented for each endpoint.

    Sorting
    -------
    `/api/netbox/?ordering=sysname` for ascending order.

    `/api/netbox/?ordering=-sysname` for descending order.

    `/api/netbox/?ordering=room__location` for ordering on related models.

    Most attributes of the result records can be used as ordering arguments.

    [1]: https://nav.readthedocs.io/en/latest/howto/using_the_api.html
    """
    return Response(get_endpoints(request))


def get_endpoints(request=None, version=1):
    """Returns all endpoints for the API"""

    apiprefix = 'api'
    prefix = '{}:{}:'.format(apiprefix, version) if version else '{}:'.format(apiprefix)
    kwargs = {'request': request}

    return {
        'account': reverse_lazy('{}account-list'.format(prefix), **kwargs),
        'accountgroup': reverse_lazy('{}accountgroup-list'.format(prefix), **kwargs),
        'alert': reverse_lazy('{}alert-list'.format(prefix), **kwargs),
        'auditlog': reverse_lazy('{}auditlog-list'.format(prefix), **kwargs),
        'arp': reverse_lazy('{}arp-list'.format(prefix), **kwargs),
        'cabling': reverse_lazy('{}cabling-list'.format(prefix), **kwargs),
        'cam': reverse_lazy('{}cam-list'.format(prefix), **kwargs),
        'interface': reverse_lazy('{}interface-list'.format(prefix), **kwargs),
        'location': reverse_lazy('{}location-list'.format(prefix), **kwargs),
        'management_profile': reverse_lazy(
            '{}management-profile-list'.format(prefix), **kwargs
        ),
        'netbox': reverse_lazy('{}netbox-list'.format(prefix), **kwargs),
        'patch': reverse_lazy('{}patch-list'.format(prefix), **kwargs),
        'prefix': reverse_lazy('{}prefix-list'.format(prefix), **kwargs),
        'prefix_routed': reverse_lazy('{}prefix-routed-list'.format(prefix), **kwargs),
        'prefix_usage': reverse_lazy('{}prefix-usage-list'.format(prefix), **kwargs),
        'room': reverse_lazy('{}room-list'.format(prefix), **kwargs),
        'servicehandler': reverse_lazy(
            '{}servicehandler-list'.format(prefix), **kwargs
        ),
        'unrecognized_neighbor': reverse_lazy(
            '{}unrecognized-neighbor-list'.format(prefix), **kwargs
        ),
        'vlan': reverse_lazy('{}vlan-list'.format(prefix), **kwargs),
        'rack': reverse_lazy('{}rack-list'.format(prefix), **kwargs),
        'module': reverse_lazy('{}module-list'.format(prefix), **kwargs),
        'vendor': reverse_lazy('{}vendor'.format(prefix), **kwargs),
        'netboxentity': reverse_lazy('{}netboxentity-list'.format(prefix), **kwargs),
        'jwt_refresh': reverse_lazy('{}jwt-refresh'.format(prefix), **kwargs),
    }


class RelatedOrderingFilter(filters.OrderingFilter):
    """
    Extends OrderingFilter to support ordering by fields in related models
    using the Django ORM __ notation
    """

    def is_valid_field(self, model, field):
        """
        Return true if the field exists within the model (or in the related
        model specified using the Django ORM __ notation)
        """
        components = field.split('__', 1)
        try:
            field = model._meta.get_field(components[0])

            # reverse relation
            if isinstance(field, _RelatedObject):
                return self.is_valid_field(field.model, components[1])

            # foreign key
            if len(components) == 2:
                remote_model = field.remote_field.model
                if remote_model:
                    return self.is_valid_field(remote_model, components[1])
            return True
        except FieldDoesNotExist:
            return False

    def remove_invalid_fields(self, queryset, ordering, view, request):
        return [
            term
            for term in ordering
            if self.is_valid_field(queryset.model, term.lstrip('-'))
        ]


class NAVAPIMixin(APIView):
    """Mixin for providing permissions and renderers"""

    authentication_classes = (
        NavBaseAuthentication,
        APIAuthentication,
        JSONWebTokenAuthentication,
    )
    permission_classes = (DefaultPermission,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    filter_backends = (filters.SearchFilter, DjangoFilterBackend, RelatedOrderingFilter)
    ordering_fields = '__all__'
    ordering = ('id',)


class ServiceHandlerViewSet(NAVAPIMixin, ViewSet):
    """List all service handlers"""

    def list(self, _request):
        """Handle list requests"""
        queryset = [self._build_object(c) for c in load_checker_classes()]
        serializer = serializers.ServiceHandlerSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, _request, pk=None):
        """Handle retrieve requests"""
        for checker in load_checker_classes():
            if checker.get_type() == pk:
                serializer = serializers.ServiceHandlerSerializer(
                    self._build_object(checker)
                )
                return Response(serializer.data)

    @staticmethod
    def _build_object(checker):
        return {
            'name': checker.get_type(),
            'ipv6_support': checker.IPV6_SUPPORT,
            'description': checker.DESCRIPTION,
        }


class LoggerMixin(object):
    """Mixin for logging API-calls"""

    def create(self, request, *args, **kwargs):
        """Log POST requests that create new objects"""
        response = super(LoggerMixin, self).create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            _logger.info('Token %s created', self.request.auth)
        return response

    def update(self, request, *args, **kwargs):
        """Log successful update (PUT and PATCH) requests

        Remember - update can create new objects with PUT
        """
        response = super(LoggerMixin, self).update(request, *args, **kwargs)
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            _logger.info(
                'Token %s updated with %s', self.request.auth, dict(self.request.data)
            )
        return response

    def destroy(self, request, *args, **kwargs):
        """Log successful DELETE requests"""
        obj = self.get_object()
        response = super(LoggerMixin, self).destroy(request, *args, **kwargs)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            _logger.info('Token %s deleted %r', self.request.auth, obj)
        return response


class AccountViewSet(NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all accounts

    Filters
    -------
    - login
    - ext_sync

    Search
    ------
    Searches in *name*
    """

    queryset = profiles.Account.objects.all()
    serializer_class = serializers.AccountSerializer
    filterset_fields = ('login', 'ext_sync')
    search_fields = ('name',)


class AccountGroupViewSet(NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all accountgroups

    Filters
    -------
    - account - filter by one or more accounts

    Search
    ------
    Searches in *name* and *description*

    Example: `accountgroup?account=abcd&account=bcde`
    """

    serializer_class = serializers.AccountGroupSerializer
    search_fields = ('name', 'description')

    def get_queryset(self):
        queryset = profiles.AccountGroup.objects.all()
        accounts = self.request.query_params.getlist('account')
        if accounts:
            queryset = queryset.filter(accounts__in=accounts).distinct()
        return queryset


class RoomViewSet(LoggerMixin, NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all rooms.

    Filters
    -------
    - description
    - location
    """

    queryset = manage.Room.objects.all()
    serializer_class = serializers.RoomSerializer
    filterset_fields = ('location', 'description')
    lookup_value_regex = '[^/]+'
    permission_classes = (RelaxedReadPermission,)


class LocationViewSet(LoggerMixin, NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all locations

    Search
    ------
    Searches in *description*

    Filters
    -------
    - id
    - parent
    """

    queryset = manage.Location.objects.all()
    serializer_class = serializers.LocationSerializer
    filterset_fields = ('id', 'parent')
    search_fields = ('description',)
    lookup_value_regex = '[^/]+'


class UnrecognizedNeighborViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists unrecognized neighbors.

    Search
    ------
    Searches in *remote_name*

    Filters
    -------
    - netbox
    - source
    """

    queryset = manage.UnrecognizedNeighbor.objects.all()
    serializer_class = serializers.UnrecognizedNeighborSerializer
    filterset_fields = ('netbox', 'source')
    search_fields = ('remote_name',)


class ManagementProfileViewSet(LoggerMixin, NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all management profiles"""

    queryset = manage.ManagementProfile.objects.all()
    serializer_class = serializers.ManagementProfileSerializer


class NetboxViewSet(LoggerMixin, NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all netboxes.

    Search
    ------
    Searches in *sysname*.

    Filters
    -------
    - category
    - ip
    - maintenance: "yes" for netboxes on maintenance, "no" for the opposite,
      unset for everything
    - organization
    - room
    - sysname
    - type__name (NB: two underscores): ^ indicates starts_with, otherwise exact match

    When the filtered item is an object, it will filter on the id.
    """

    queryset = manage.Netbox.objects.all().prefetch_related("info_set")
    serializer_class = serializers.NetboxSerializer
    filterset_fields = (
        'sysname',
        'room',
        'organization',
        'category',
        'room__location',
    )
    filter_backends = NAVAPIMixin.filter_backends + (
        NetboxIsOnMaintenanceFilterBackend,
    )
    search_fields = ('sysname',)

    def destroy(self, request, *args, **kwargs):
        """Override the deletion process

        The background processes of NAV will execute the deletion if deleted_at
        is set
        """
        obj = self.get_object()
        obj.deleted_at = datetime.now()
        obj.save()
        _logger.info('Token %s set deleted at for %r', self.request.auth, obj)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        """Implement basic filtering on type__name

        If more custom filters are requested create a filterbackend:
        http://www.django-rest-framework.org/api-guide/filtering/#example
        """
        qs = super(NetboxViewSet, self).get_queryset()
        params = self.request.query_params
        if 'type__name' in params:
            value = params.get('type__name')
            if value.startswith('^'):
                qs = qs.filter(type__name__istartswith=value[1:])
            else:
                qs = qs.filter(type__name=value)
        ip = params.get('ip', None)
        if ip:
            try:
                addr = IP(ip)
            except ValueError:
                raise IPParseError
            oper = '=' if addr.len() == 1 else '<<'
            expr = "netbox.ip {} '{}'".format(oper, addr)
            qs = qs.extra(where=[expr])

        return qs


class InterfaceFilterClass(FilterSet):
    """Exists only to have a sane implementation of multiple choice filters"""

    netbox = ModelMultipleChoiceFilter(queryset=manage.Netbox.objects.all())

    class Meta(object):
        model = manage.Interface
        fields = (
            'ifname',
            'ifindex',
            'ifoperstatus',
            'netbox',
            'trunk',
            'ifadminstatus',
            'iftype',
            'baseport',
            'module__name',
            'vlan',
        )


class InterfaceFragmentRenderer(TemplateHTMLRenderer):
    media_type = 'text/x-nav-html'
    template_name = 'ipdevinfo/port-details-api-frag.html'


class InterfaceViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all interfaces.

    Search
    ------
    Searches in *ifalias*, *ifdescr* and *ifname*

    Filters
    -------
    - baseport
    - ifadminstatus
    - ifindex
    - ifname
    - ifoperstatus
    - iftype
    - netbox
    - trunk
    - vlan
    - module__name
    - ifclass=[swport, gwport, physicalport, trunk]

    Detail routes
    -------------
    - last_used: interface/<id>/last_used/
    - metrics: interface/<id>/metrics/

    Example: `/api/1/interface/?netbox=91&ifclass=trunk&ifclass=swport`
    """

    queryset = manage.Interface.objects.prefetch_related('swport_vlans__vlan').all()
    search_fields = ('ifalias', 'ifdescr', 'ifname')

    # NaturalIfnameFilter returns a list, so IfClassFilter needs to come first
    filter_backends = NAVAPIMixin.filter_backends + (IfClassFilter, NaturalIfnameFilter)
    filterset_class = InterfaceFilterClass

    # Logged-in users must be able to access this API to use the ipdevinfo ports tool
    permission_classes = (RelaxedReadPermission,)

    def get_serializer_class(self):
        request = self.request
        if request.query_params.get('last_used'):
            return serializers.InterfaceWithCamSerializer
        else:
            return serializers.InterfaceSerializer

    def get_renderers(self):
        if self.action == 'retrieve':
            self.renderer_classes += (InterfaceFragmentRenderer,)
        return super(InterfaceViewSet, self).get_renderers()

    @action(detail=True)
    def metrics(self, _request, pk=None):
        """List all metrics for this interface

        We don't want to include this by default as that will spam the Graphite
        backend with requests.
        """
        return Response(self.get_object().get_port_metrics())

    @action(detail=True)
    def last_used(self, _request, pk=None):
        """Return last used timestamp for this interface

        If still in use this will return datetime.max as per
        DateTimeInfinityField
        """
        try:
            serialized = serializers.CamSerializer(
                self.get_object().get_last_cam_record()
            )
            return Response({'last_used': serialized.data.get('end_time')})
        except manage.Cam.DoesNotExist:
            return Response({'last_used': None})


class PatchViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all patches

    Search
    ------
    Searches in the cables *jack*-field

    Filters
    -------
    - cabling: The cable id
    - cabling__room: The room id
    - interface: The interface id
    - interface__netbox: The netbox id

    ### (Silly) Example
    `patch/?interface__netbox=138&interface=337827&search=a`
    """

    filter_backends = NAVAPIMixin.filter_backends + (NaturalIfnameFilter,)

    queryset = cabling.Patch.objects.select_related(
        'cabling__room', 'interface__netbox'
    ).all()
    serializer_class = serializers.PatchSerializer
    filterset_fields = ('cabling', 'cabling__room', 'interface', 'interface__netbox')
    search_fields = ('cabling__jack',)


class CablingViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all cables.

    Search
    ------
    Searches in *jack*, *target_room*, *building*

    Filters
    -------
    - available: *set this to list only cables that are not patched*
    - building
    - category
    - jack
    - room
    - target_room

    """

    serializer_class = serializers.CablingSerializer
    filterset_fields = ('room', 'jack', 'building', 'target_room', 'category')
    search_fields = ('jack', 'target_room', 'building')

    def get_queryset(self):
        queryset = cabling.Cabling.objects.all()
        not_patched = self.request.query_params.get('available', None)
        if not_patched:
            queryset = queryset.filter(patches=None)

        return queryset


SQL_OVERLAPS = "(start_time, end_time) OVERLAPS ('{}'::TIMESTAMP, '{}'::TIMESTAMP)"
SQL_BETWEEN = "'{}'::TIMESTAMP BETWEEN start_time AND end_time"


class MachineTrackerViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Abstract base ViewSet for ARP and CAM tables"""

    def get_queryset(self):
        """Filter on custom parameters"""
        queryset = self.model_class.objects.all()
        active = self.request.query_params.get('active', None)
        starttime, endtime = get_times(self.request)

        if active:
            queryset = queryset.filter(end_time=INFINITY)
        elif starttime and not endtime:
            queryset = queryset.extra(where=[SQL_BETWEEN.format(starttime)])
        elif starttime and endtime:
            queryset = queryset.extra(where=[SQL_OVERLAPS.format(starttime, endtime)])

        # Support wildcard filtering on mac
        queryset = self._parse_mac_to_queryset(
            self.request.query_params.get('mac'), queryset
        )

        return queryset

    @staticmethod
    def _parse_mac_to_queryset(mac, queryset):
        if not mac:
            return queryset

        try:
            mac = MacPrefix(mac, min_prefix_len=2)
        except ValueError as e:
            raise exceptions.ParseError("mac: %s" % e)

        low, high = mac[0], mac[-1]
        return queryset.extra(
            where=["mac BETWEEN %s AND %s"], params=[str(low), str(high)]
        )


class CamViewSet(MachineTrackerViewSet):
    """Lists CAM records.

    *Because the number of CAM records often is huge, the API does not support
    fetching all and will ask you to use a filter if you try.*

    Filters
    -------
    - `active`: *set this to list only records that are still active. Enabling
    this will **ignore** any start- and endtime filters present in the same
    request.*
    - `starttime`: *if set without endtime: lists all active records at that
      timestamp*
    - `endtime`: *must be set with starttime: lists all active records in the
      period between starttime and endtime*
    - `ifindex`
    - `mac`: *supports prefix filtering - for instance "mac=aa:aa:aa" will
       return all records where the mac address starts with aa:aa:aa*
    - `netbox`
    - `port`

    For timestamp formats, see the [iso8601 module
    doc](https://pypi.python.org/pypi/iso8601) and <https://xkcd.com/1179/>.
    `end_time` timestamps shown as `"9999-12-31T23:59:59.999"` denote records
    that are still active.
    """

    model_class = manage.Cam
    serializer_class = serializers.CamSerializer
    filterset_fields = ('netbox', 'ifindex', 'port')

    def list(self, request):
        """Override list so that we can control what is returned"""
        if not request.query_params:
            return Response(
                "Cam records are numerous - use a filter",
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super(CamViewSet, self).list(request)


class ArpViewSet(MachineTrackerViewSet):
    """Lists ARP records.

    *Because the number of ARP records often is huge, the API does not support
    fetching all and will ask you to use a filter if you try.*

    Filters
    -------

    - `active`: *set this to list only records that are still active. Enabling
    this will **ignore** any start- and endtime filters present in the same
    request.*
    - `starttime`: *if set without endtime: lists all active records at that
      timestamp*
    - `endtime`: *must be set with starttime: lists all active records in the
      period between starttime and endtime*
    - `ip`: *Allows filtering by both individual IP addresses and subnet ranges.
      Single IP example: "ip=2001:db8:a0b:12f0::1"
      Subnet example: "ip=10.0.42.0/24"*
    - `mac`: *supports prefix filtering - for instance "mac=aa:aa:aa" will
       return all records where the mac address starts with aa:aa:aa*
    - `netbox`
    - `prefix`

    For timestamp formats, see the [iso8601 module
    doc](https://pypi.python.org/pypi/iso8601) and <https://xkcd.com/1179/>.
    `end_time` timestamps shown as `"9999-12-31T23:59:59.999"` denote records
    that are still active.
    """

    model_class = manage.Arp
    serializer_class = serializers.ArpSerializer
    filterset_fields = ('netbox', 'prefix')

    def list(self, request):
        """Override list so that we can control what is returned"""
        if not request.query_params:
            return Response(
                "Arp records are numerous - use a filter",
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super(ArpViewSet, self).list(request)

    def get_queryset(self):
        """Customizes handling of the ip address filter"""
        queryset = super(ArpViewSet, self).get_queryset()
        ip = self.request.query_params.get('ip', None)
        if ip:
            try:
                addr = IP(ip)
            except ValueError:
                raise IPParseError
            oper = '=' if addr.len() == 1 else '<<'
            expr = "arp.ip {} '{}'".format(oper, addr)
            queryset = queryset.extra(where=[expr])

        return queryset


class VlanViewSet(NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all vlans.

    Search
    ------
    Searches in *net_ident* and *description*

    Filters
    -------
    - description
    - net_type
    - net_ident
    - organization
    - usage
    - vlan
    """

    queryset = manage.Vlan.objects.all()
    serializer_class = serializers.VlanSerializer
    filterset_fields = [
        'vlan',
        'net_type',
        'net_ident',
        'description',
        'organization',
        'usage',
    ]
    search_fields = ['net_ident', 'description']


class PrefixFilterClass(FilterSet):
    contains_address = CharFilter(method="contains_address_filter")
    net_address = CharFilter(method="is_net_address")

    def contains_address_filter(self, queryset, field_name, value):
        if not value:
            return queryset
        if not is_valid_cidr(value):
            raise ValidationError(
                {"contains_address": ["Value must be a valid CIDR address"]}
            )
        where_string = "inet '{}' <<= netaddr".format(value)
        return queryset.extra(where=[where_string], order_by=['net_address'])

    def is_net_address(self, queryset, field_name, value):
        if not value:
            return queryset
        if not is_valid_cidr(value):
            raise ValidationError(
                {"net_address": ["Value must be a valid CIDR address"]}
            )
        return queryset.filter(net_address=value)

    class Meta(object):
        model = manage.Prefix
        fields = (
            'vlan',
            'net_address',
            'vlan__vlan',
        )


class PrefixViewSet(NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all prefixes.

    Filters
    -------
    - net_address
    - vlan
    - vlan__vlan: *Filters on the vlan number of the vlan*
    - contains_address

    """

    queryset = manage.Prefix.objects.all()
    serializer_class = serializers.PrefixSerializer
    filterset_class = PrefixFilterClass

    @action(detail=False)
    def search(self, request):
        """Do string-like prefix searching. Currently only supports net_address."""
        net_address = request.GET.get('net_address', None)
        if not net_address or net_address is None:
            return Response("Empty search", status=status.HTTP_400_BAD_REQUEST)
        query = "SELECT * FROM prefix WHERE text(netaddr) LIKE %s"
        # Note: We assume people always know the beginning of a prefix, and
        # need to drill down further. Hence the wildcard ("%") at the end.
        queryset = manage.Prefix.objects.raw(query, [net_address + "%"])
        results = self.get_serializer(queryset, many=True)
        return Response(results.data)


class RoutedPrefixList(NAVAPIMixin, ListAPIView):
    """Lists all routed prefixes. A router has category *GSW* or *GW*

    Filters
    -------
    - family: *either 4 or 6, else both will be listed*

    """

    _router_categories = ['GSW', 'GW']
    serializer_class = serializers.PrefixSerializer

    def get_queryset(self):
        prefixes = manage.Prefix.objects.filter(
            gwport_prefixes__interface__netbox__category__in=self._router_categories
        )
        if self.request.GET.get('family'):
            prefixes = prefixes.extra(
                where=['family(netaddr)=%s'], params=[self.request.GET['family']]
            )
        return prefixes


def get_times(request):
    """Gets start and endtime from request

    As we use no timezone in NAV, remove it from parsed timestamps
    :param request: django.http.HttpRequest
    """
    starttime = request.GET.get('starttime')
    endtime = request.GET.get('endtime')
    try:
        if starttime:
            starttime = iso8601.parse_date(starttime).replace(tzinfo=None)
        if endtime:
            endtime = iso8601.parse_date(endtime).replace(tzinfo=None)
    except iso8601.ParseError:
        raise Iso8601ParseError

    return starttime, endtime


class PrefixUsageList(NAVAPIMixin, ListAPIView):
    """Lists the usage of prefixes. This means how many addresses are in use
    in the prefix.

    Usage is only the result of active/max and is kinda silly on v6-addresses.

    Filters
    -------
    - scope: *limit results to a specific scope*
    - family: *limit results to family (either 4 or 6)*
    - starttime: *If set without endtime, will find active addresses at that
            time. If set *with* endtime, defines the interval to find active
            addresses. Format is [iso8601][1].*
    - endtime: *Must be set together with starttime. Defines the interval to
            find active addresses. Format is [iso8601][1].*

    See also the [iso8601 module doc](https://pypi.python.org/pypi/iso8601).

    Examples:

    - `?starttime=2016-02-02`
    - `?starttime=2016-02-02T15:00:00` - default Zulu time.
    - `?starttime=2016-02-02T15:00:00%2B05` - plus needs to be encoded.

    [1]: https://xkcd.com/1179/
    """

    serializer_class = serializers.PrefixUsageSerializer

    # RelatedOrderingFilter does not work with the custom pagination
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)

    # Logged-in users must be able to access this API to use the subnet matrix tool
    permission_classes = (RelaxedReadPermission,)

    def get(self, request, *args, **kwargs):
        """Override get method to verify url parameters"""
        get_times(request)
        return super(PrefixUsageList, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """Filter for ip family"""
        if 'scope' in self.request.GET:
            queryset = manage.Prefix.objects.within(
                self.request.GET.get('scope')
            ).order_by('net_address')
        elif self.request.GET.get('family'):
            queryset = manage.Prefix.objects.extra(
                where=['family(netaddr)=%s'], params=[self.request.GET['family']]
            )
        else:
            queryset = manage.Prefix.objects.all()

        # Filter prefixes that is smaller than minimum prefix length
        results = [
            p for p in queryset if IP(p.net_address).len() >= MINIMUMPREFIXLENGTH
        ]

        return results

    def get_serializer(self, data, *args, **kwargs):
        """Populate the serializer with usages based on the prefix list"""
        kwargs['context'] = self.get_serializer_context()
        starttime, endtime = get_times(self.request)
        usages = prefix_collector.fetch_usages(data, starttime, endtime)
        serializer_class = self.get_serializer_class()
        return serializer_class(
            usages, *args, context=self.get_serializer_context(), many=True
        )


class PrefixUsageDetail(NAVAPIMixin, APIView):
    """Makes prefix usage accessible from api"""

    @staticmethod
    def get(request, prefix):
        """Handles get request for prefix usage"""

        try:
            ip_prefix = IP(prefix)
        except ValueError:
            return Response("Bad prefix", status=status.HTTP_400_BAD_REQUEST)

        if ip_prefix.len() < MINIMUMPREFIXLENGTH:
            return Response("Prefix is too small", status=status.HTTP_400_BAD_REQUEST)

        starttime, endtime = get_times(request)
        db_prefix = get_object_or_404(manage.Prefix, net_address=prefix)
        serializer = serializers.PrefixUsageSerializer(
            prefix_collector.fetch_usage(db_prefix, starttime, endtime)
        )

        return Response(serializer.data)


class AlertFragmentRenderer(TemplateHTMLRenderer):
    """Renders a html fragment for an alert

    To use this you specify mime-type 'text/x-nav-html' in the accept header
    Does not work for list views
    """

    media_type = 'text/x-nav-html'

    def get_template_context(self, data, renderer_context):
        """Populate the context used for rendering the template

        :param dict data: The serialized alert
        :param dict renderer_context: Existing context
        """

        if 'id' not in data:
            return data

        # Put the alert object in the context
        data['alert'] = event.AlertHistory.objects.get(pk=data['id'])

        netboxid = data.get('netbox')
        if netboxid:
            # Replace netbox (the netboxid) with netbox (the object)
            data.update({'netbox': manage.Netbox.objects.get(pk=netboxid)})
        return data


class AlertHistoryViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all alerts.

    Filters
    -------
    - stateless: *also lists stateless alerts (alerts without end time)*
    - stateless_threshold: *hours back in time to fetch stateless alerts*

    Example: `?stateless=1&stateless_threshold=1000`

    Headers
    -------
    By setting the _Accept_ header field to `text/x-nav-html` you will get a
    html-representation of the alert suitable for including in web-pages. This
    only works on _retrieve_ operations, not _list_ operations.

    If the response is an empty string, this means that a template for that
    alert does not exist.
    """

    filter_backends = (AlertHistoryFilterBackend,)
    # Logged-in users must be able to access this API to use the status tool
    permission_classes = (RelaxedReadPermission,)
    model = event.AlertHistory
    serializer_class = alert_serializers.AlertHistorySerializer
    base_queryset = base = event.AlertHistory.objects.prefetch_related(
        "variables", "netbox__groups"
    ).select_related(
        "netbox",
        "alert_type",
        "event_type",
        "acknowledgement",
        "source",
    )

    def get_renderers(self):
        if self.action == 'retrieve':
            self.renderer_classes += (AlertFragmentRenderer,)
        return super(AlertHistoryViewSet, self).get_renderers()

    def get_queryset(self):
        """Gets an AlertHistory QuerySet"""
        if self.is_single_alert_by_primary_key():
            return self.base_queryset
        elif not self.request.query_params.get('stateless', False):
            return self.base_queryset.unresolved()
        else:
            return self._get_stateless_queryset()

    def _get_stateless_queryset(self):
        hours = int(
            self.request.query_params.get('stateless_threshold', STATELESS_THRESHOLD)
        )
        if hours < 1:
            raise ValueError("hours must be at least 1")
        threshold = datetime.now() - timedelta(hours=hours)
        stateless = Q(start_time__gte=threshold) & Q(end_time__isnull=True)
        return self.base_queryset.filter(stateless | UNRESOLVED)

    def get_template_names(self):
        """Get the template name based on the alerthist object"""
        alert = self.get_object()
        template_names = []
        try:
            template_names.append(
                'alertmsg/{a.event_type}/{a.alert_type.name}.html'.format(a=alert)
            )
        except AttributeError:
            pass

        template_names.extend(
            ['alertmsg/{a.event_type}/base.html'.format(a=alert), 'alertmsg/base.html']
        )
        return template_names

    def is_single_alert_by_primary_key(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        return lookup_url_kwarg in self.kwargs


class RackViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all environment racks.

    Search
    ------
    Searches in *rackname*

    Filters
    -------
    - id
    - room
    - rackname

    """

    queryset = rack.Rack.objects.all()
    serializer_class = serializers.RackSerializer
    filterset_fields = ['room', 'rackname']
    search_fields = ['rackname']


def get_or_create_token(request):
    """Gets an existing token or creates a new one. If the old token has
    expired, create a new one.

    :type request: django.http.HttpRequest
    """
    account = get_account(request)
    if account.is_admin():
        from nav.models.api import APIToken

        token, _ = APIToken.objects.get_or_create(
            client=account,
            expires__gte=datetime.now(),
            defaults={'token': auth_token(), 'expires': datetime.now() + EXPIRE_DELTA},
        )
        return HttpResponse(token.token)
    else:
        return HttpResponse(
            'You must log in to get a token', status=status.HTTP_403_FORBIDDEN
        )


def get_nav_version(request):
    """Returns the version of the running NAV software

    :type request: django.http.HttpRequest
    """
    return JsonResponse({"version": VERSION})


class ModuleViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all modules.

    Filters
    -------
    - netbox
    - device__serial

    Example: `/api/1/module/?netbox=91&device__serial=AB12345`
    """

    queryset = manage.Module.objects.all()
    filter_backends = NAVAPIMixin.filter_backends
    filterset_fields = (
        'netbox',
        'device__serial',
    )
    serializer_class = serializers.ModuleSerializer


class VendorLookup(NAVAPIMixin, APIView):
    """Lookup vendor names for MAC addresses.

    This endpoint allows you to look up vendor names for MAC addresses.
    It can be used with either a GET or POST request.

    For GET requests, the MAC address must be provided via the query parameter `mac`.
    This only supports one MAC address at a time.

    For POST requests, the MAC addresses must be provided in the request body
    as a JSON array. This supports multiple MAC addresses.

    Responds with a JSON dict mapping the MAC addresses to the corresponding vendors.
    The MAC addresses will have the format `aa:bb:cc:dd:ee:ff`. If the vendor for a
    given MAC address is not found, it will be omitted from the response.
    If no mac address was supplied, an empty dict will be returned.

    Example GET request: `/api/1/vendor/?mac=aa:bb:cc:dd:ee:ff`

    Example GET response: `{"aa:bb:cc:dd:ee:ff": "Vendor A"}`

    Example POST request:
        `/api/1/vendor/` with body `["aa:bb:cc:dd:ee:ff", "11:22:33:44:55:66"]`

    Example POST response:
        `{"aa:bb:cc:dd:ee:ff": "Vendor A", "11:22:33:44:55:66": "Vendor B"}`
    """

    @staticmethod
    def get(request):
        mac = request.GET.get('mac', None)
        if not mac:
            return Response({})

        try:
            validated_mac = MacAddress(mac)
        except ValueError:
            return Response(
                f"Invalid MAC address: '{mac}'", status=status.HTTP_400_BAD_REQUEST
            )

        results = get_vendor_names([validated_mac])
        return Response(results)

    @staticmethod
    def post(request):
        if isinstance(request.data, list):
            mac_addresses = request.data

        # This adds support for requests via the browseable API
        elif isinstance(request.data, QueryDict):
            json_string = request.data.get('_content')
            if not json_string:
                return Response("Empty JSON body", status=status.HTTP_400_BAD_REQUEST)
            try:
                mac_addresses = json.loads(json_string)
            except json.JSONDecodeError:
                return Response("Invalid JSON", status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(mac_addresses, list):
                return Response(
                    "Invalid request body. Must be a JSON array of MAC addresses",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                "Invalid request body. Must be a JSON array of MAC addresses",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validated_mac_addresses = validate_mac_addresses(mac_addresses)
        except ValueError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        results = get_vendor_names(validated_mac_addresses)
        return Response(results)


@django.db.transaction.atomic
def get_vendor_names(mac_addresses: Sequence[MacAddress]) -> dict[str, str]:
    """Get vendor names for a sequence of MAC addresses.

    :param mac_addresses: Sequence of MAC addresses in a valid format
        (e.g., "aa:bb:cc:dd:ee:ff").
    :return: A dictionary mapping MAC addresses to vendor names. If the vendor for a
        given MAC address is not found, it will be omitted from the response.
    """
    # Skip SQL query if no MAC addresses are provided
    if not mac_addresses:
        return {}

    # Generate the VALUES part of the SQL query dynamically
    values = ", ".join(f"('{mac}'::macaddr)" for mac in mac_addresses)

    # Construct the full SQL query
    query = f"""
        SELECT mac, vendor
        FROM (
            VALUES
                {values}
        ) AS temp_macaddrs(mac)
        INNER JOIN oui ON trunc(temp_macaddrs.mac) = oui.oui;
    """

    cursor = django.db.connection.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()

    # row[0] is mac address, row[1] is vendor name
    return {str(row[0]): row[1] for row in rows}


def validate_mac_addresses(mac_addresses: Sequence[str]) -> list[MacAddress]:
    """Validates MAC addresses and returns them as MacAddress objects.

    :param mac_addresses: MAC addresses as strings in a valid format
        (e.g., "aa:bb:cc:dd:ee:ff").
    :return: List of MacAddress objects.
    :raises ValueError: If any MAC address is invalid.
    """
    validated_macs = []
    invalid_macs = []
    for mac in mac_addresses:
        try:
            validated_macs.append(MacAddress(mac))
        except ValueError:
            invalid_macs.append(mac)
    if invalid_macs:
        raise ValueError(f"Invalid MAC address(es): {', '.join(invalid_macs)}")
    return validated_macs


class NetboxEntityViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for viewing NetboxEntities.

    Filters
    -------
    - netbox
    - physical_class

    Example: `/api/netboxentity/?netbox=109&physical_class=3`
    """

    queryset = manage.NetboxEntity.objects.all()
    serializer_class = serializers.NetboxEntitySerializer
    filterset_fields = ['netbox', 'physical_class']


class JWTRefreshViewSet(NAVAPIMixin, APIView):
    """
    Accepts a valid refresh token.
    Returns a new refresh token and an access token.
    """

    permission_classes = []

    def post(self, request):
        if not LOCAL_JWT_IS_CONFIGURED:
            return Response("Invalid token", status=status.HTTP_403_FORBIDDEN)
        # This adds support for requests via the browseable API.
        # Browseble API sends QueryDict with _content key.
        # Tests send QueryDict without _content key so it can be treated
        # as a regular dict.
        if isinstance(request.data, QueryDict) and '_content' in request.data:
            json_string = request.data.get('_content')
            if not json_string:
                return Response("Empty JSON body", status=status.HTTP_400_BAD_REQUEST)
            try:
                data = json.loads(json_string)
            except json.JSONDecodeError:
                return Response("Invalid JSON", status=status.HTTP_400_BAD_REQUEST)
            if not isinstance(data, dict):
                return Response(
                    "Invalid request body. Must be a JSON dict",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif isinstance(request.data, dict):
            data = request.data
        else:
            return Response(
                "Invalid request body. Must be a JSON dict",
                status=status.HTTP_400_BAD_REQUEST,
            )

        incoming_token = data.get('refresh_token')
        if incoming_token is None:
            return Response("Missing token", status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(incoming_token, str):
            return Response("Invalid token", status=status.HTTP_400_BAD_REQUEST)

        token_hash = hash_token(incoming_token)
        try:
            # Hash must be in the database for the token to be valid
            db_token = JWTRefreshToken.objects.get(hash=token_hash)
        except JWTRefreshToken.DoesNotExist:
            return Response("Invalid token", status=status.HTTP_403_FORBIDDEN)

        if db_token.revoked:
            return Response(
                "This token has been revoked", status=status.HTTP_403_FORBIDDEN
            )

        try:
            claims = jwt.decode(
                incoming_token,
                JWT_PUBLIC_KEY,
                audience=JWT_NAME,
                issuer=JWT_NAME,
                algorithms=["RS256"],
            )
        except jwt.InvalidSignatureError:
            return Response("Invalid signature", status=status.HTTP_403_FORBIDDEN)
        except jwt.InvalidAudienceError:
            return Response("Invalid audience", status=status.HTTP_403_FORBIDDEN)
        except jwt.InvalidIssuerError:
            return Response("Invalid issuer", status=status.HTTP_403_FORBIDDEN)
        except jwt.ExpiredSignatureError:
            return Response("Token has expired", status=status.HTTP_403_FORBIDDEN)
        except jwt.ImmatureSignatureError:
            return Response("Token is not yet active", status=status.HTTP_403_FORBIDDEN)
        # base exception for jwt.decode
        except jwt.InvalidTokenError:
            return Response("Invalid token", status=status.HTTP_403_FORBIDDEN)

        access_token = generate_access_token(claims)
        refresh_token = generate_refresh_token(claims)

        new_claims = decode_token(refresh_token)
        new_hash = hash_token(refresh_token)
        db_token.hash = new_hash
        db_token.expires = datetime.fromtimestamp(new_claims['exp'])
        db_token.activates = datetime.fromtimestamp(new_claims['nbf'])
        db_token.last_used = datetime.now()
        db_token.save()

        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
        }
        return Response(response_data)

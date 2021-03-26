# Copyright (C) 2013 Uninett AS
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
# pylint: disable=R0903, R0901, R0904
"""Views for the NAV API"""

from datetime import datetime, timedelta
import logging

from IPy import IP
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.db.models.fields.related import ManyToOneRel as _RelatedObject
from django.db.models.fields import FieldDoesNotExist
import iso8601

from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from django_filters.filters import ModelMultipleChoiceFilter
from rest_framework import status, filters, viewsets, exceptions
from rest_framework.decorators import (api_view, renderer_classes, list_route,
                                       detail_route)
from rest_framework.reverse import reverse_lazy
from rest_framework.renderers import (JSONRenderer, BrowsableAPIRenderer,
                                      TemplateHTMLRenderer)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.generics import ListAPIView, get_object_or_404

from nav.models import manage, event, cabling, rack, profiles
from nav.models.fields import INFINITY, UNRESOLVED
from nav.web.servicecheckers import load_checker_classes
from nav.util import auth_token

from nav.buildconf import VERSION
from nav.web.api.v1 import serializers, alert_serializers
from nav.web.status2 import STATELESS_THRESHOLD
from nav.macaddress import MacPrefix
from .auth import APIPermission, APIAuthentication, NavBaseAuthentication
from .helpers import prefix_collector
from .filter_backends import (AlertHistoryFilterBackend, IfClassFilter,
                              NaturalIfnameFilter,
                              NetboxIsOnMaintenanceFilterBackend,)

EXPIRE_DELTA = timedelta(days=365)
MINIMUMPREFIXLENGTH = 4

_logger = logging.getLogger(__name__)


class Iso8601ParseError(exceptions.ParseError):
    default_detail = ('Wrong format on timestamp. See '
                      'https://pypi.python.org/pypi/iso8601')


class IPParseError(exceptions.ParseError):
    default_detail = ('ip field must be a valid IPv4 or IPv6 host address or '
                      'network prefix')


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
    prefix = ('{}:{}:'.format(apiprefix, version)
              if version else '{}:'.format(apiprefix))
    kwargs = {'request': request}

    return {
        'account': reverse_lazy('{}account-list'.format(prefix), **kwargs),
        'accountgroup': reverse_lazy('{}accountgroup-list'.format(prefix), **kwargs),
        'alert': reverse_lazy('{}alert-list'.format(prefix), **kwargs),
        'auditlog': reverse_lazy('{}auditlog-list'.format(prefix), **kwargs),
        'arp': reverse_lazy('{}arp-list'.format(prefix), **kwargs),
        'cabling': reverse_lazy('{}cabling-list'.format(prefix), **kwargs),
        'cam': reverse_lazy('{}cam-list'.format(prefix), **kwargs),
        'interface': reverse_lazy('{}interface-list'.format(prefix),
                                  **kwargs),
        'location': reverse_lazy('{}location-list'.format(prefix), **kwargs),
        'management_profile': reverse_lazy('{}management-profile-list'.format(prefix),
                                           **kwargs),
        'netbox': reverse_lazy('{}netbox-list'.format(prefix), **kwargs),
        'patch': reverse_lazy('{}patch-list'.format(prefix), **kwargs),
        'prefix': reverse_lazy('{}prefix-list'.format(prefix), **kwargs),
        'prefix_routed': reverse_lazy('{}prefix-routed-list'.format(prefix),
                                      **kwargs),
        'prefix_usage': reverse_lazy('{}prefix-usage-list'.format(prefix),
                                     **kwargs),
        'room': reverse_lazy('{}room-list'.format(prefix), **kwargs),
        'servicehandler': reverse_lazy('{}servicehandler-list'.format(prefix),
                                       **kwargs),
        'unrecognized_neighbor': reverse_lazy('{}unrecognized-neighbor-list'.format(prefix), **kwargs),
        'vlan': reverse_lazy('{}vlan-list'.format(prefix), **kwargs),
        'rack': reverse_lazy('{}rack-list'.format(prefix), **kwargs),
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
                try:
                    remote_model = field.remote_field.model
                except AttributeError:  # Django <= 1.8
                    remote_model = field.rel.to
                if remote_model:
                    return self.is_valid_field(remote_model, components[1])
            return True
        except FieldDoesNotExist:
            return False

    def remove_invalid_fields(self, queryset, ordering, view, request):
        return [term for term in ordering
                if self.is_valid_field(queryset.model, term.lstrip('-'))]


class NAVAPIMixin(APIView):
    """Mixin for providing permissions and renderers"""
    authentication_classes = (NavBaseAuthentication, APIAuthentication)
    permission_classes = (APIPermission,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,
                       RelatedOrderingFilter)
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
                    self._build_object(checker))
                return Response(serializer.data)

    @staticmethod
    def _build_object(checker):
        return {
            'name': checker.get_type(),
            'ipv6_support': checker.IPV6_SUPPORT,
            'description': checker.DESCRIPTION
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
            _logger.info('Token %s updated with %s', self.request.auth,
                         dict(self.request.data))
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
    filter_fields = ('login', 'ext_sync')
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
    filter_fields = ('location', 'description')


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
    filter_fields = ('id', 'parent')
    search_fields = ('description',)


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
    filter_fields = ('netbox', 'source')
    search_fields = ('remote_name', )

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
    queryset = manage.Netbox.objects.all()
    serializer_class = serializers.NetboxSerializer
    filter_fields = ('ip', 'sysname', 'room', 'organization', 'category',
                     'room__location')
    filter_backends = (
        NAVAPIMixin.filter_backends + (NetboxIsOnMaintenanceFilterBackend,)
    )
    search_fields = ('sysname', )

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

        return qs


class InterfaceFilterClass(FilterSet):
    """Exists only to have a sane implementation of multiple choice filters"""
    netbox = ModelMultipleChoiceFilter(
        queryset=manage.Netbox.objects.all())

    class Meta(object):
        model = manage.Interface
        fields = ('ifname', 'ifindex', 'ifoperstatus', 'netbox', 'trunk',
                  'ifadminstatus', 'iftype', 'baseport', 'module__name', 'vlan')


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
    - last_used: interface/<id\>/last_used/
    - metrics: interface/<id\>/metrics/

    Example: `/api/1/interface/?netbox=91&ifclass=trunk&ifclass=swport`
    """
    queryset = manage.Interface.objects.all()
    search_fields = ('ifalias', 'ifdescr', 'ifname')

    # NaturalIfnameFilter returns a list, so IfClassFilter needs to come first
    filter_backends = NAVAPIMixin.filter_backends + (IfClassFilter, NaturalIfnameFilter)
    filter_class = InterfaceFilterClass

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

    @detail_route()
    def metrics(self, _request, pk=None):
        """List all metrics for this interface

        We don't want to include this by default as that will spam the Graphite
        backend with requests.
        """
        return Response(self.get_object().get_port_metrics())

    @detail_route()
    def last_used(self, _request, pk=None):
        """Return last used timestamp for this interface

        If still in use this will return datetime.max as per
        DateTimeInfinityField
        """
        try:
            serialized = serializers.CamSerializer(
                self.get_object().get_last_cam_record())
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

    filter_backends = NAVAPIMixin.filter_backends + (NaturalIfnameFilter, )

    queryset = cabling.Patch.objects.select_related(
        'cabling__room', 'interface__netbox').all()
    serializer_class = serializers.PatchSerializer
    filter_fields = ('cabling', 'cabling__room',
                     'interface', 'interface__netbox')
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
    filter_fields = ('room', 'jack', 'building', 'target_room', 'category')
    search_fields = ('jack', 'target_room', 'building')

    def get_queryset(self):
        queryset = cabling.Cabling.objects.all()
        not_patched = self.request.query_params.get('available', None)
        if not_patched:
            queryset = queryset.filter(patch=None)

        return queryset


SQL_OVERLAPS = ("(start_time, end_time) OVERLAPS "
                "('{}'::TIMESTAMP, '{}'::TIMESTAMP)")
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
            queryset = queryset.extra(
                where=[SQL_OVERLAPS.format(starttime, endtime)])

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
            where=["mac BETWEEN %s AND %s"],
            params=[str(low), str(high)]
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
    filter_fields = ('netbox', 'ifindex', 'port')

    def list(self, request):
        """Override list so that we can control what is returned"""
        if not request.query_params:
            return Response("Cam records are numerous - use a filter",
                            status=status.HTTP_400_BAD_REQUEST)
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
    - `ip`
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
    filter_fields = ('netbox', 'prefix')

    def list(self, request):
        """Override list so that we can control what is returned"""
        if not request.query_params:
            return Response("Arp records are numerous - use a filter",
                            status=status.HTTP_400_BAD_REQUEST)
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
    filter_fields = ['vlan', 'net_type', 'net_ident', 'description',
                     'organization', 'usage']
    search_fields = ['net_ident', 'description']


class PrefixViewSet(NAVAPIMixin, viewsets.ModelViewSet):
    """Lists all prefixes.

    Filters
    -------
    - net_address
    - vlan
    - vlan__vlan: *Filters on the vlan number of the vlan*

    """
    queryset = manage.Prefix.objects.all()
    serializer_class = serializers.PrefixSerializer
    filter_fields = ('vlan', 'net_address', 'vlan__vlan')

    @list_route()
    def search(self, request):
        """Do string-like prefix searching. Currently only supports net_address.

        """
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
            gwportprefix__interface__netbox__category__in=
            self._router_categories)
        if self.request.GET.get('family'):
            prefixes = prefixes.extra(where=['family(netaddr)=%s'],
                                      params=[self.request.GET['family']])
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
                where=['family(netaddr)=%s'],
                params=[self.request.GET['family']])
        else:
            queryset = manage.Prefix.objects.all()

        # Filter prefixes that is smaller than minimum prefix length
        results = [p for p in queryset
                   if IP(p.net_address).len() >= MINIMUMPREFIXLENGTH]

        return results

    def get_serializer(self, data, *args, **kwargs):
        """Populate the serializer with usages based on the prefix list"""
        kwargs['context'] = self.get_serializer_context()
        starttime, endtime = get_times(self.request)
        usages = prefix_collector.fetch_usages(data, starttime, endtime)
        serializer_class = self.get_serializer_class()
        return serializer_class(
            usages, *args, context=self.get_serializer_context(), many=True)


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
            return Response("Prefix is too small",
                            status=status.HTTP_400_BAD_REQUEST)

        starttime, endtime = get_times(request)
        db_prefix = get_object_or_404(manage.Prefix, net_address=prefix)
        serializer = serializers.PrefixUsageSerializer(
            prefix_collector.fetch_usage(db_prefix, starttime, endtime))

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
            data.update({
                'netbox': manage.Netbox.objects.get(pk=netboxid)
            })
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
    model = event.AlertHistory
    serializer_class = alert_serializers.AlertHistorySerializer
    base_queryset = base = event.AlertHistory.objects.prefetch_related(
        "variables", "netbox__groups"
    ).select_related(
        "netbox", "alert_type", "event_type", "acknowledgement", "source",
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
        hours = int(self.request.query_params.get('stateless_threshold',
                                                  STATELESS_THRESHOLD))
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
                'alertmsg/{a.event_type}/{a.alert_type.name}.html'.format(
                    a=alert))
        except AttributeError:
            pass

        template_names.extend([
            'alertmsg/{a.event_type}/base.html'.format(a=alert),
            'alertmsg/base.html'
        ])
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
    filter_fields = ['room', 'rackname']
    search_fields = ['rackname']


def get_or_create_token(request):
    """Gets an existing token or creates a new one. If the old token has
    expired, create a new one.

    :type request: django.http.HttpRequest
    """
    if request.account.is_admin():
        from nav.models.api import APIToken
        token, _ = APIToken.objects.get_or_create(
            client=request.account, expires__gte=datetime.now(),
            defaults={'token': auth_token(),
                      'expires': datetime.now() + EXPIRE_DELTA})
        return HttpResponse(str(token))
    else:
        return HttpResponse('You must log in to get a token',
                            status=status.HTTP_403_FORBIDDEN)


def get_nav_version(request):
    """Returns the version of the running NAV software

    :type request: django.http.HttpRequest
    """
    return JsonResponse({"version": VERSION})

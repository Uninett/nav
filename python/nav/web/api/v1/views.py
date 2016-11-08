# Copyright (C) 2013 UNINETT AS
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
# pylint: disable=R0903, R0901, R0904
"""Views for the NAV API"""

from IPy import IP
from django.http import HttpResponse
from django.template import loader, RequestContext, TemplateDoesNotExist
from django.db.models import Q
from django.db.models.related import RelatedObject
from django.db.models.fields import FieldDoesNotExist
from datetime import datetime, timedelta
import iso8601
from django.http.response import Http404

from provider.utils import long_token
from rest_framework import status, filters, viewsets, exceptions
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.reverse import reverse_lazy
from rest_framework.renderers import (JSONRenderer, BrowsableAPIRenderer,
                                      TemplateHTMLRenderer)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.generics import ListAPIView
from nav.models.api import APIToken
from nav.models import manage, event, cabling
from nav.models.fields import INFINITY, UNRESOLVED
from nav.web.servicecheckers import load_checker_classes

from nav.web.api.v1 import serializers, alert_serializers
from .auth import APIPermission, APIAuthentication, NavBaseAuthentication
from .helpers import prefix_collector
from .filter_backends import AlertHistoryFilterBackend, NaturalIfnameFilter
from nav.web.status2 import STATELESS_THRESHOLD

EXPIRE_DELTA = timedelta(days=365)
MINIMUMPREFIXLENGTH = 4

import logging
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
    The NAV API is currently read only.

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

    [1]: https://nav.uninett.no/doc/latest/howto/using_the_api.html
    """
    return Response(get_endpoints(request))


def get_endpoints(request=None, version=1):
    """Returns all endpoints for the API"""

    apiprefix = 'api'
    prefix = ('{}:{}:'.format(apiprefix, version)
              if version else '{}:'.format(apiprefix))
    kwargs = {'request': request}

    return {
        'alert': reverse_lazy('{}alerthistory-list'.format(prefix), **kwargs),
        'arp': reverse_lazy('{}arp-list'.format(prefix), **kwargs),
        'cabling': reverse_lazy('{}cabling-list'.format(prefix), **kwargs),
        'cam': reverse_lazy('{}cam-list'.format(prefix), **kwargs),
        'interface': reverse_lazy('{}interface-list'.format(prefix),
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
        'vlan': reverse_lazy('{}vlan-list'.format(prefix), **kwargs),
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
            field, _parent_model, _direct, _m2m = \
                model._meta.get_field_by_name(components[0])

            # reverse relation
            if isinstance(field, RelatedObject):
                return self.is_valid_field(field.model, components[1])

            # foreign key
            if field.rel and len(components) == 2:
                return self.is_valid_field(field.rel.to, components[1])
            return True
        except FieldDoesNotExist:
            return False

    def remove_invalid_fields(self, queryset, ordering, view):
        return [term for term in ordering
                if self.is_valid_field(queryset.model, term.lstrip('-'))]


class NAVAPIMixin(APIView):
    """Mixin for providing permissions and renderers"""
    authentication_classes = (NavBaseAuthentication, APIAuthentication)
    permission_classes = (APIPermission,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend,
                       RelatedOrderingFilter)


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


class RoomViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all rooms.

    Filters
    -------
    - description
    - location
    """
    queryset = manage.Room.objects.all()
    serializer_class = serializers.RoomSerializer
    filter_fields = ('location', 'description')


class NetboxViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all netboxes.

    Search
    ------
    Searches in *sysname*.

    Filters
    -------
    - category
    - ip
    - organization
    - room
    - sysname

    When the filtered item is an object, it will filter on the id.
    """
    queryset = manage.Netbox.objects.all()
    serializer_class = serializers.NetboxSerializer
    filter_fields = ('ip', 'sysname', 'room', 'organization', 'category')
    search_fields = ('sysname', )


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
    """
    queryset = manage.Interface.objects.all()
    serializer_class = serializers.InterfaceSerializer
    filter_fields = ('ifname', 'ifindex', 'ifoperstatus', 'netbox', 'trunk',
                     'ifadminstatus', 'iftype', 'baseport')
    search_fields = ('ifalias', 'ifdescr', 'ifname')


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
        not_patched = self.request.QUERY_PARAMS.get('available', None)
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
        active = self.request.QUERY_PARAMS.get('active', None)
        starttime, endtime = get_times(self.request)

        if active:
            queryset = queryset.filter(end_time=INFINITY)
        elif starttime and not endtime:
            queryset = queryset.extra(where=[SQL_BETWEEN.format(starttime)])
        elif starttime and endtime:
            queryset = queryset.extra(
                where=[SQL_OVERLAPS.format(starttime, endtime)])

        return queryset


class CamViewSet(MachineTrackerViewSet):
    """Lists all cam records.

    Filters
    -------
    - `active`: *set this to list only records that has not ended. This will
      then ignore any start and endtimes set*
    - `starttime`: *if set without endtime: lists all active records at that
      timestamp*
    - `endtime`: *must be set with starttime: lists all active records in the
      period between starttime and endtime*
    - `ifindex`
    - `mac`
    - `netbox`
    - `port`

    For timestamp formats, see the [iso8601 module
    doc](https://pypi.python.org/pypi/iso8601) and <https://xkcd.com/1179/>.
    `end_time` timestamps shown as `"9999-12-31T23:59:59.999"` denote records
    that are still active.

    """
    model_class = manage.Cam
    serializer_class = serializers.CamSerializer
    filter_fields = ('mac', 'netbox', 'ifindex', 'port')


class ArpViewSet(MachineTrackerViewSet):
    """Lists all arp records.

    Filters
    -------

    - `active`: *set this to list only records that has not ended. This will
      then ignore any start and endtimes set*
    - `starttime`: *if set without endtime: lists all active records at that
      timestamp*
    - `endtime`: *must be set with starttime: lists all active records in the
      period between starttime and endtime*
    - `ip`
    - `mac`
    - `netbox`
    - `prefix`

    For timestamp formats, see the [iso8601 module
    doc](https://pypi.python.org/pypi/iso8601) and <https://xkcd.com/1179/>.
    `end_time` timestamps shown as `"9999-12-31T23:59:59.999"` denote records
    that are still active.

    """
    model_class = manage.Arp
    serializer_class = serializers.ArpSerializer
    filter_fields = ('mac', 'netbox', 'prefix')

    def get_queryset(self):
        """Customizes handling of the ip address filter"""
        queryset = super(ArpViewSet, self).get_queryset()
        ip = self.request.QUERY_PARAMS.get('ip', None)
        if ip:
            try:
                addr = IP(ip)
            except ValueError:
                raise IPParseError
            oper = '=' if addr.len() == 1 else '<<'
            queryset = queryset.extra(where=["ip {} '{}'".format(oper, addr)])

        return queryset


class VlanViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
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


class PrefixViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
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

    def get(self, request, *args, **kwargs):
        """Override get method to verify url parameters"""
        get_times(request)
        return super(PrefixUsageList, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """Filter for ip family"""
        if 'scope' in self.request.GET:
            queryset = (manage.Prefix.objects.within(
                self.request.GET.get('scope')).select_related('vlan')
                        .order_by('net_address'))
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

    def list(self, request, *args, **kwargs):
        """Delivers a list of usage objects as a response

        The queryset contains prefixes, but we use a custom object for
        representing the usage statistics for the prefix. Thus we need to
        convert the filtered prefixes to the custom object format.

        Also we need to run the prefix collector after paging to avoid
        unnecessary usage calculations
        """
        page = self.paginate_queryset(self.filter_queryset(self.get_queryset()))
        starttime, endtime = get_times(self.request)
        prefixes = prefix_collector.fetch_usages(
            page.object_list, starttime, endtime)

        if page is not None:
            page.object_list = prefixes
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(prefixes, many=True)

        return Response(serializer.data)


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
        db_prefix = manage.Prefix.objects.get(net_address=prefix)
        serializer = serializers.PrefixUsageSerializer(
            prefix_collector.fetch_usage(db_prefix, starttime, endtime))

        return Response(serializer.data)


class AlertFragmentRenderer(TemplateHTMLRenderer):
    """Renders a html fragment for an alert

    To use this you specify mime-type 'text/navfragment' in the accept header
    Does not work for list views
    """
    media_type = 'text/x-navfragment'

    def resolve_template(self, template_names):
        """We most probably do not have all templates defined"""
        try:
            return loader.select_template(template_names)
        except TemplateDoesNotExist:
            raise Http404('Fragment template does not exist')

    def resolve_context(self, data, request, _response):
        """Populate the context used for rendering the template

        :type request: rest_framework.request.Request
        :type _response: rest_framework.request.Response
        :param dict data: The serialized alert
        """
        # Put the alert object in the context
        data['alert'] = event.AlertHistory.objects.get(pk=data['id'])

        netboxid = data.get('netbox')
        if netboxid:
            # Replace netbox (the netboxid) with netbox (the object)
            data.update({
                'netbox': manage.Netbox.objects.get(pk=netboxid)
            })
        return RequestContext(request, data)


class AlertHistoryViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Lists all alerts.

    Filters
    -------
    - stateless: *also lists stateless alerts (alerts without end time)*
    - stateless_threshold: *hours back in time to fetch stateless alerts*

    Example: `?stateless=1&stateless_threshold=1000`

    By setting the mime-type to `text/navfragment` you will get a
    html-representation of the alert suitable for including in web-pages.
    This only works on _retrieve_ operations, not _list_ operations.
    """

    filter_backends = (AlertHistoryFilterBackend,)
    model = event.AlertHistory
    serializer_class = alert_serializers.AlertHistorySerializer

    def get_renderers(self):
        if self.action == 'retrieve':
            self.renderer_classes += (AlertFragmentRenderer,)
        return super(AlertHistoryViewSet, self).get_renderers()

    def get_queryset(self):
        """Gets an AlertHistory QuerySet"""
        if not self.request.QUERY_PARAMS.get('stateless', False):
            return event.AlertHistory.objects.unresolved().select_related()
        else:
            return self._get_stateless_queryset()

    def _get_stateless_queryset(self):
        hours = int(self.request.QUERY_PARAMS.get('stateless_threshold',
                                                  STATELESS_THRESHOLD))
        if hours < 1:
            raise ValueError("hours must be at least 1")
        threshold = datetime.now() - timedelta(hours=hours)
        stateless = Q(start_time__gte=threshold) & Q(end_time__isnull=True)
        return event.AlertHistory.objects.filter(
            stateless | UNRESOLVED).select_related()

    def get_object(self, queryset=None):
        return super(AlertHistoryViewSet, self).get_object(self.model)

    def get_template_names(self):
        """Get the template name based on the alerthist object"""
        alert = self.get_object()
        return ['alertmsg/{}/{}.html'.format(
            alert.event_type, alert.alert_type.name)]


def get_or_create_token(request):
    """Gets an existing token or creates a new one. If the old token has
    expired, create a new one.

    :type request: django.http.HttpRequest
    """
    if request.account.is_admin():
        token, _ = APIToken.objects.get_or_create(
            client=request.account, expires__gte=datetime.now(),
            defaults={'token': long_token(),
                      'expires': datetime.now() + EXPIRE_DELTA})
        return HttpResponse(str(token))
    else:
        return HttpResponse('You must log in to get a token',
                            status=status.HTTP_403_FORBIDDEN)

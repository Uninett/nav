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
from datetime import datetime, timedelta
import iso8601

from provider.utils import long_token
from rest_framework import status, filters, viewsets
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from nav.models.api import APIToken
from nav.models.manage import Room, Netbox, Prefix, Interface

from .auth import APIPermission, APIAuthentication
from .serializers import (RoomSerializer, NetboxSerializer, PrefixSerializer,
                          PrefixUsageSerializer, InterfaceSerializer)
from .helpers import prefix_collector

EXPIRE_DELTA = timedelta(days=365)
MINIMUMPREFIXLENGTH = 4


@api_view(('GET',))
def api_root(request, format=None):
    """Create api root for informing about possible endpoints"""
    return Response({
        'room': reverse('v1-api-rooms', request=request),
        'netbox': reverse('v1-api-netboxes', request=request),
        'interface': reverse('v1-api-interfaces', request=request),
        'prefix': reverse('v1-api-prefixes', request=request),
        'prefix_routed': reverse('v1-api-prefixes-routed', request=request),
    })


class NAVAPIMixin(APIView):
    """Mixin for providing permissions and renderers"""
    authentication_classes = (APIAuthentication,)
    permission_classes = (APIPermission,)
    renderer_classes = (JSONRenderer,)
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)


class RoomViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Makes rooms accessible from api"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    filter_fields = ('location', 'description')


class NetboxViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Makes netboxes accessible from api"""
    queryset = Netbox.objects.all()
    serializer_class = NetboxSerializer
    filter_fields = ('sysname', 'room', 'organization', 'category')
    search_fields = ('sysname', )


class InterfaceViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Makes interfaces accessible from api"""
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    filter_fields = ('ifname', 'ifindex', 'ifoperstatus', 'netbox', 'trunk',
                     'ifadminstatus', 'iftype', 'baseport')
    search_fields = ('ifalias', 'ifdescr', 'ifname')


class PrefixViewSet(NAVAPIMixin, viewsets.ReadOnlyModelViewSet):
    """Makes prefixes available from api"""
    queryset = Prefix.objects.all()
    serializer_class = PrefixSerializer
    filter_fields = ('vlan', 'net_address', 'vlan__vlan')


class RoutedPrefixList(NAVAPIMixin, ListAPIView):
    """Fetches routed prefixes"""
    _router_categories = ['GSW', 'GW']
    serializer_class = PrefixSerializer

    def get_queryset(self):
        prefixes = Prefix.objects.filter(
            gwportprefix__interface__netbox__category__in=
            self._router_categories)
        if 'family' in self.request.GET:
            prefixes = prefixes.extra(where=['family(netaddr)=%s'],
                                      params=[self.request.GET.get('family')])

        return prefixes


def get_times(request):
    """Gets start and endtime from request"""
    starttime = request.GET.get('starttime')
    endtime = request.GET.get('endtime')
    if starttime:
        starttime = iso8601.parse_date(starttime)
    if endtime:
        endtime = iso8601.parse_date(endtime)
    return starttime, endtime


class PrefixUsageList(NAVAPIMixin, APIView):
    """Makes prefix usage for all prefixes available"""
    def get(self, request):
        prefixes = []

        try:
            starttime, endtime = get_times(request)
        except (ValueError, iso8601.ParseError):
            return Response(
                'start or endtime not formatted correctly. Use iso8601 format',
                status=status.HTTP_400_BAD_REQUEST)

        for prefix in Prefix.objects.all():
            tmp_prefix = IP(prefix.net_address)
            if tmp_prefix.len() >= MINIMUMPREFIXLENGTH:
                prefixes.append(tmp_prefix)

        serializer = PrefixUsageSerializer(
            prefix_collector.fetch_usages(prefixes, starttime, endtime))

        return Response(serializer.data)


class PrefixUsageDetail(NAVAPIMixin, APIView):
    """Makes prefix usage accessible from api"""
    def get(self, request, prefix):
        """Handles get request for prefix usage"""

        try:
            prefix = IP(prefix)
        except ValueError:
            return Response("Bad prefix", status=status.HTTP_400_BAD_REQUEST)

        if prefix.len() < MINIMUMPREFIXLENGTH:
            return Response("Prefix is too small",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            starttime, endtime = get_times(request)
        except (ValueError, iso8601.ParseError):
            return Response(
                'start or endtime not formatted correctly. Use iso8601 format',
                status=status.HTTP_400_BAD_REQUEST)

        serializer = PrefixUsageSerializer(
            prefix_collector.fetch_usage(prefix, starttime, endtime))

        return Response(serializer.data)


def get_or_create_token(request):
    """Gets an existing token or creates a new one

    :type request: django.http.HttpRequest
    """
    if request.account.is_admin():
        token, _ = APIToken.objects.get_or_create(
            client=request.account,
            defaults={'token': long_token(),
                      'expires': datetime.now() + EXPIRE_DELTA})
        return HttpResponse(str(token))
    else:
        return HttpResponse('You must log in to get a token',
                            status=status.HTTP_403_FORBIDDEN)

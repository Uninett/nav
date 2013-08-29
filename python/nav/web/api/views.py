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
# pylint: disable=R0903
"""Views for the NAV API"""

from IPy import IP
from django.http import HttpResponse
from datetime import datetime, timedelta
import iso8601

from provider.utils import long_token
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from nav.models.api import APIToken
from nav.models.manage import Room, Netbox

from .auth import APIPermission, APIAuthentication
from .serializers import (RoomSerializer, NetboxSerializer,
                          PrefixUsageSerializer)
from .helpers import prefix_collector

EXPIRE_DELTA = timedelta(days=365)


class NAVAPIMixin(APIView):
    """Mixin for providing permissions and renderers"""
    authentication_classes = (APIAuthentication,)
    permission_classes = (APIPermission,)
    renderer_classes = (JSONRenderer,)


class RoomList(NAVAPIMixin, ListAPIView):
    """Makes rooms accessible from api"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class RoomDetail(NAVAPIMixin, RetrieveAPIView):
    """Makes room details accessible from api"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


class NetboxList(NAVAPIMixin, ListAPIView):
    """Makes netboxes accessible from api"""
    queryset = Netbox.objects.all()
    serializer_class = NetboxSerializer


class NetboxDetail(NAVAPIMixin, RetrieveAPIView):
    """Makes netbox accessible from api"""
    queryset = Netbox.objects.all()
    serializer_class = NetboxSerializer


class PrefixUsageDetail(NAVAPIMixin, APIView):
    """Makes prefix usage accessible from api"""

    MINIMUMPREFIXLENGTH = 4

    def get_times(self, request):
        """Gets start and endtime from request"""
        starttime = request.GET.get('starttime')
        endtime = request.GET.get('endtime')
        if starttime:
            starttime = iso8601.parse_date(starttime)
        if endtime:
            endtime = iso8601.parse_date(endtime)
        return starttime, endtime

    def get(self, request, prefix):
        """Handles get request for prefix usage"""

        try:
            prefix = IP(prefix)
        except ValueError:
            return Response("Bad prefix", status=status.HTTP_400_BAD_REQUEST)

        if len(prefix) < self.MINIMUMPREFIXLENGTH:
            return Response("Prefix is too small",
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            starttime, endtime = self.get_times(request)
        except ValueError:
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
    if request.account.is_admin_account():
        token, _ = APIToken.objects.get_or_create(
            client=request.account,
            defaults={'token': long_token(),
                      'expires': datetime.now() + EXPIRE_DELTA})
        return HttpResponse(str(token))
    else:
        return HttpResponse('You must log in to get a token',
                            status=status.HTTP_403_FORBIDDEN)

#
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

from django.http import HttpResponse
from datetime import datetime, timedelta

from provider.utils import long_token
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from nav.models.api import APIToken
from nav.models.manage import Room, Netbox

from .auth import APIPermission, APIAuthentication
from .serializers import RoomSerializer, NetboxSerializer

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


class PrefixUsageList(APIView):
    """For future usage"""
    renderer_classes = [JSONRenderer]

    def get(self):
        """Fetch stuff, create serializer, return data"""
        return Response()


def get_or_create_token(request):
    """Gets an existing token or creates a new one"""
    if request.account.is_admin_account():
        token, _ = APIToken.objects.get_or_create(
            client=request.account,
            defaults={'token': long_token(),
                      'expires': datetime.now() + EXPIRE_DELTA})
        return HttpResponse(str(token))
    else:
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)

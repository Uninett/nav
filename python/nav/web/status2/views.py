#
# Copyright (C) 2014 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import View

from rest_framework import viewsets, filters
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from nav.models.event import AlertHistory
from . import serializers


class StatusView(View):
    def get(self, request):
        alerts = AlertHistory.objects.unresolved().order_by('-start_time')
        return render_to_response(
            'status2/status.html',
            {
                'title': 'NAV - Status',
                'navpath': [('Home', '/'), ('Status', '')],

                'alerts': alerts,
            },
            RequestContext(request)
        )


class StatusAPIMixin(APIView):
    """Mixin for providing permissions and renderers"""
    renderer_classes = (JSONRenderer,)
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)


class AlertHistoryViewSet(StatusAPIMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AlertHistory.objects.unresolved().select_related(depth=1)
    serializer_class = serializers.AlertHistorySerializer
    filter_fields = ('event_type', 'netbox__organization', 'netbox__category')

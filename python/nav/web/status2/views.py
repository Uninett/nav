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
"""NAV status app views"""
import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import View
from django.db.models import Q

from rest_framework import viewsets, filters
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from nav.models.event import AlertHistory, AlertType
from nav.models.manage import Category
from nav.models.fields import UNRESOLVED
from . import serializers

STATELESS_THRESHOLD = 24

class StatusView(View):
    """Generic Status view"""

    def get(self, request):
        """Produces a list view of AlertHistory entries"""
        return render_to_response(
            'status2/status.html',
            {
                'title': 'NAV - Status',
                'navpath': [('Home', '/'), ('Status', '')],
                'alerttypes': AlertType.objects.all().order_by(
                    'event_type', 'name'),
                'categories': Category.objects.all()
            },
            RequestContext(request)
        )


class StatusAPIMixin(APIView):
    """Mixin for providing permissions and renderers"""
    renderer_classes = (JSONRenderer,)
    filter_backends = (filters.DjangoFilterBackend,)


class AlertHistoryViewSet(StatusAPIMixin, viewsets.ReadOnlyModelViewSet):
    """API view for listing AlertHistory entries"""

    queryset = AlertHistory.objects.none()
    serializer_class = serializers.AlertHistorySerializer

    def get_queryset(self):
        """Produces a queryset customized from the query parameters"""
        if not self.request.QUERY_PARAMS.get('stateless', False):
            qset = AlertHistory.objects.unresolved().select_related(depth=1)
        else:
            qset = self._get_stateless_queryset()

        qset = self._multivalue_filter(qset)
        return qset

    def _get_stateless_queryset(self):
        hours = int(self.request.QUERY_PARAMS.get('stateless_threshold',
                                                  STATELESS_THRESHOLD))
        if hours < 1:
            raise ValueError("hours must be at least 1")
        threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
        stateless = Q(start_time__gte=threshold) & Q(end_time__isnull=True)
        return AlertHistory.objects.filter(
            stateless | UNRESOLVED).select_related(depth=1)

    MULTIVALUE_FILTERS = {
        'event_type': 'event_type',
        'organization': 'netbox__organization',
        'category': 'netbox__category',
        'alert_type': 'alert_type__name',
    }

    def _multivalue_filter(self, qset):
        for arg, field in self.MULTIVALUE_FILTERS.items():
            values = self.request.QUERY_PARAMS.getlist(arg, None)
            if values:
                filtr = field + '__in'
                qset = qset.filter(**{filtr: values})
        return qset


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
from rest_framework import viewsets

from nav.web.api.v1.views import NAVAPIMixin

from .models import LogEntry


class LogEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = LogEntry
        fields = [
            'timestamp',
            'verb',
            'summary',
            'subsystem',
            'before',
            'after',
        ]
        read_only_fields = ['timestamp']


class NAVDefaultsMixin(object):
    authentication_classes = NAVAPIMixin.authentication_classes
    permission_classes = NAVAPIMixin.permission_classes
    renderer_classes = NAVAPIMixin.renderer_classes
    filter_backends = NAVAPIMixin.filter_backends


class LogEntryViewSet(NAVDefaultsMixin, viewsets.ReadOnlyModelViewSet):
    """Read only api endpoint for logentries.

    Logentries are created behind the scenes by the subsystems themselves."""

    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer

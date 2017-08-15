#
# Copyright (C) 2015 UNINETT AS
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
"""Custom filter backends"""

from . import alert_serializers
from rest_framework import filters

from nav import natsort
from nav.models.manage import Location


class NaturalIfnameFilter(filters.OrderingFilter):
    """Filter naturally on interface ifname"""

    def filter_queryset(self, request, queryset, view):
        """Filter on ifname if it exists as an ordering parameter"""

        interface_ifnames = ['interface__ifname', '-interface__ifname']
        ifnames = ['ifname', '-ifname']
        intersection = (set(self.get_ordering(request)) &
                        set(interface_ifnames + ifnames))

        try:
            match_field = intersection.pop()
        except KeyError:
            return queryset
        else:
            if match_field in interface_ifnames:
                lookup = lambda x: natsort.split(x.interface.ifname)
            if match_field in ifnames:
                lookup = lambda x: natsort.split(x.ifname)
            return sorted(queryset,
                          key=lookup,
                          reverse=match_field.startswith('-'))


class AlertHistoryFilterBackend(filters.BaseFilterBackend):
    """
    Custom filtering of AlertHistory results.

    Turns out we can't get the DjangoFilterBackend to support OR/IN filters,
    which is what we want for several of the fields in the AlertHistory
    model; therefore we customize everythin. Egads, Brain!
    """
    MULTIVALUE_FILTERS = {
        'event_type': 'event_type',
        'organization': 'netbox__organization',
        'category': 'netbox__category',
        'alert_type': 'alert_type__name',
        'device_group': 'netbox__groups__id',
        'location': 'netbox__room__location',
    }

    MULTIVALUE_EXCLUDES = {
        'not_event_type': 'event_type',
        'not_organization': 'netbox__organization',
        'not_category': 'netbox__category',
        'not_alert_type': 'alert_type__name',
        'not_device_group': 'netbox__groups__id',
        'not_location': 'netbox__room__location',
    }

    def filter_queryset(self, request, queryset, view):
        for arg, field in self.MULTIVALUE_FILTERS.items():
            values = request.QUERY_PARAMS.getlist(arg, None)
            if values:
                # Locations are hierarchial - must include descendants
                if arg == 'location':
                    values = get_descendants(values)
                filtr = field + '__in'
                queryset = queryset.filter(**{filtr: values})

        for arg, field in self.MULTIVALUE_EXCLUDES.items():
            values = request.QUERY_PARAMS.getlist(arg, None)
            if values:
                # Locations are hierarchial - must include descendants
                if arg == 'not_location':
                    values = get_descendants(values)
                filtr = field + '__in'
                queryset = queryset.exclude(**{filtr: values})

        acked = request.QUERY_PARAMS.get("acknowledged", False)
        if not acked:
            queryset = queryset.filter(acknowledgement__isnull=True)

        on_maintenance = request.QUERY_PARAMS.get("on_maintenance", False)
        if not on_maintenance:
            is_on_maintenance = (
                alert_serializers.AlertHistorySerializer.is_on_maintenance)

            # It's time we stop being a queryset, since we now need to filter
            # on computed values
            queryset = [i for i in queryset if not is_on_maintenance(i)]

        return queryset


def get_descendants(parents):
    """Returns a list of all descendants for the parents including themselves"""
    locations = []
    for parent in parents:
        try:
            location = Location.objects.get(pk=parent)
        except Location.DoesNotExist:
            pass
        else:
            locations.extend([l.pk for l in
                              location.get_descendants(include_self=True)])

    return list(set(locations))

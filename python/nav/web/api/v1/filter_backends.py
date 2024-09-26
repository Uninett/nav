#
# Copyright (C) 2015 Uninett AS
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
"""Custom filter backends"""

import operator

# reduce is removed in python 3, import it from functools
from functools import reduce as reduce3
from rest_framework import filters
from django.db.models import Q

from nav import natsort
from nav.models.manage import Location
from . import alert_serializers

__all__ = ['NaturalIfnameFilter', 'IfClassFilter', 'AlertHistoryFilterBackend']


class IfClassFilter(filters.BaseFilterBackend):
    """Filter on ifclasses

    An ifclass is a fantasy construct that tells you if this interface is a
    swport, gwport or physical port (can be zero or more)
    """

    def filter_queryset(self, request, queryset, view):
        """Filter on interface class/type

        NB: Needs a Queryset as queryset, other filters that return lists will
        break this.

        Using the methods (is_swport, is_gwport etc) on the Interface model
        means doing everything in python in stead of letting the database do it,
        so we reimplement them here with Q-objects.
        """
        filters = {
            'swport': Q(baseport__isnull=False),
            'gwport': Q(gwport_prefixes__isnull=False),
            'physicalport': Q(ifconnectorpresent=True),
            'trunk': Q(trunk=True),
        }

        if 'ifclass' in request.query_params:
            matching_filters = set(request.query_params.getlist('ifclass')) & set(
                filters
            )
            if matching_filters:
                q = reduce3(operator.or_, [filters[f] for f in matching_filters])
                queryset = queryset.filter(q).distinct()

        return queryset


class NaturalIfnameFilter(filters.OrderingFilter):
    """Filter naturally on interface ifname"""

    def filter_queryset(self, request, queryset, view):
        """Filter on ifname if it exists as an ordering parameter"""

        interface_ifnames = ['interface__ifname', '-interface__ifname']
        ifnames = ['ifname', '-ifname']
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        intersection = set(ordering) & set(interface_ifnames + ifnames)

        try:
            match_field = intersection.pop()
        except KeyError:
            return queryset
        else:
            if match_field in interface_ifnames:
                lookup = lambda x: natsort.split(x.interface.ifname)
            if match_field in ifnames:
                lookup = lambda x: natsort.split(x.ifname)
            return sorted(queryset, key=lookup, reverse=match_field.startswith('-'))


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
        'severity': 'severity',
    }

    MULTIVALUE_EXCLUDES = {
        'not_event_type': 'event_type',
        'not_organization': 'netbox__organization',
        'not_category': 'netbox__category',
        'not_alert_type': 'alert_type__name',
        'not_device_group': 'netbox__groups__id',
        'not_location': 'netbox__room__location',
        'not_severity': 'severity',
    }

    def filter_queryset(self, request, queryset, view):
        if view.is_single_alert_by_primary_key():
            # no really, the client asked for a specific single alert, screw
            # all the other filters!
            return queryset

        for arg, field in self.MULTIVALUE_FILTERS.items():
            values = request.query_params.getlist(arg, None)
            if values:
                # Locations are hierarchial - must include descendants
                if arg == 'location':
                    values = _get_descendants(values)
                filtr = field + '__in'
                queryset = queryset.filter(**{filtr: values})

        for arg, field in self.MULTIVALUE_EXCLUDES.items():
            values = request.query_params.getlist(arg, None)
            if values:
                # Locations are hierarchial - must include descendants
                if arg == 'not_location':
                    values = _get_descendants(values)
                filtr = field + '__in'
                queryset = queryset.exclude(**{filtr: values})

        acked = request.query_params.get("acknowledged", False)
        if not acked:
            queryset = queryset.filter(acknowledgement__isnull=True)

        on_maintenance = request.query_params.get("on_maintenance", False)
        if not on_maintenance:
            is_on_maintenance = (
                alert_serializers.AlertHistorySerializer.is_on_maintenance
            )

            # It's time we stop being a queryset, since we now need to filter
            # on computed values
            queryset = [i for i in queryset if not is_on_maintenance(i)]

        return queryset


class NetboxIsOnMaintenanceFilterBackend(filters.BaseFilterBackend):
    """ """

    def filter_queryset(self, request, queryset, view):
        show_on_maintenance = request.query_params.get('maintenance', None)
        if show_on_maintenance not in ('yes', 'no'):
            return queryset
        on_maintenance = True if show_on_maintenance == 'yes' else False
        return queryset.on_maintenance(on_maintenance)


def _get_descendants(parents):
    """Returns a list of all descendants for the parents including themselves"""
    locations = []
    for parent in parents:
        try:
            location = Location.objects.get(pk=parent)
        except Location.DoesNotExist:
            pass
        else:
            locations.extend(
                [
                    location.pk
                    for location in location.get_descendants(include_self=True)
                ]
            )

    return list(set(locations))

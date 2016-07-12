# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 UNINETT AS
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

"""
API specific code for the private IPAM API. Exports a router for easy mounting.

"""


from rest_framework import viewsets, status, routers
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.db.models import Q, query
import operator
import collections
from copy import copy
from IPy import IPSet, IP

from .prefix_tree import make_tree

from nav.models.manage import Prefix
from nav.web.api.v1.serializers import PrefixSerializer
from nav.web.api.v1.views import get_times


from nav.web.api.v1.helpers import prefix_collector


# TODO: Consider moving most of this to web.api namespace, since there's no
# reason this shouldn't be public
# TODO: Handle search by time so we can scope the usage stats
# TODO: Generate usage by reusing report/API helpers from nav.web.api.v1.helpers
# TODO: Find available stuff

# Default types to include in the generated prefix tree
DEFAULT_TREE_PARAMS = {
    "rfc1918": False,
    "ipv6": False,
    "ipv4": False
}


# Utility class (builder pattern) to get the Prefixes we want. Applies any
# filters upon finalize. (We could do this in-place, e.g. replace the queryset
# each time, but we would then lose all filters upon methods that reset the
# queryset, e.g. manager methods like 'within').
class PrefixQuerysetBuilder(object):
    def __init__(self, queryset=None):
        if queryset is None:
            queryset = Prefix.objects.all()
        self.queryset = queryset
        self.is_realized = False
        self.filters = Q()

    def filter(self, *args, **kwargs):
        q = Q(*args, **kwargs)
        return this._filter(q)

    def _filter(self, q_object, disjoint=False):
        if disjoint:
            self.filters.add(q_object, Q.OR)
        else:
            self.filters.add(q_object, Q.AND)
        return self

    def finalize(self):
        "Returns the queryset with all filters applied"
        return self.queryset.filter(self.filters)

    # Filter methods
    def organization(self, organization):
        if organization is None:
            return self
        q = Q(vlan__organization_id__icontains=organization)
        return self._filter(q)

    def description(self, description):
        if description is None:
            return self
        q = Q(vlan__description__icontains=description)
        return self._filter(q)

    def vlan_number(self, vlan_number):
        if vlan_number is None:
            return self
        q = Q(vlan__vlan=vlan_number)
        return self._filter(q)

    def net_type(self, net_type_or_net_types):
        if net_type_or_net_types is None:
            return self
        types = net_type_or_net_types
        if not isinstance(types, list):
            types = [types]
        q = Q(vlan__net_type__in=types)
        return self._filter(q)

    def search(self, query):
        if query is None:
            return self
        q = Q()
        q.add(Q(vlan__description__icontains=query), Q.OR)
        q.add(Q(vlan__organization__id__icontains=query), Q.OR)
        return self._filter(q)

    # Mutating methods, e.g. resets the queryset
    def within(self, prefix):
        "Sets the queryset to every Prefix within a certain prefix"
        if prefix is None:
            return self
        self.queryset = Prefix.objects.within(prefix)
        return self

class PrefixViewSet(viewsets.ViewSet):
    serializer = PrefixSerializer
    search_fields = ("vlan__description")

    def get_queryset(self):
        # Extract filters etc
        net_types = self.request.QUERY_PARAMS.getlist("net_type", ["scope"])
        search = self.request.QUERY_PARAMS.get("search", None)
        organization = self.request.QUERY_PARAMS.get("organization", None)
        vlan_number = self.request.QUERY_PARAMS.get("vlan", None)
        # Build queryset
        queryset = PrefixQuerysetBuilder()
        queryset.net_type(net_types)
        queryset.search(search)
        queryset.organization(organization)
        queryset.vlan_number(vlan_number)
        return queryset.finalize()

    @detail_route(methods=["get"])
    def usage(self, request, *args, **kwargs):
        pk = kwargs.pop("pk", None)
        # TODO: error handling
        prefix = Prefix.objects.get(pk=pk)
        max_addr = IP(prefix.net_address).len()
        active_addr = prefix_collector.collect_active_ip(prefix)
        payload = {
            "max_addr": max_addr,
            "active_addr": active_addr,
            "usage": 1.0 * active_addr / max_addr,
            "pk": pk
        }
        return Response(payload, status=status.HTTP_200_OK)

    # TODO add serializer
    def list(self, request, *args, **kwargs):
        prefixes = self.get_queryset()
        # parse "?type=" args
        args = copy(DEFAULT_TREE_PARAMS)
        _types = self.request.QUERY_PARAMS.getlist("type", ["ipv4"])
        _args = {_type: True for _type in _types if _type in DEFAULT_TREE_PARAMS}
        args.update(_args)
        # handle timespans
        starttime, endtime = get_times(self.request)
        result = make_tree(prefixes, starttime, endtime, **args)
        return Response(result.fields["children"], status=status.HTTP_200_OK)

# TODO Everything below is pretty horrible and should be taken out in the woods
# to be dealt with. Refactor soon.

class PrefixFinderSet(viewsets.ViewSet):
    serializer = PrefixSerializer

    # TODO Implement search for length?
    # TODO Filter all IPv6 addresses, as they tend to give us overflow errors
    def get_queryset(self):
        # Extract filters
        prefix = self.request.QUERY_PARAMS.get("prefix", None)
        organization = self.request.QUERY_PARAMS.get("organization", None)
        # Build queryset
        queryset = PrefixQuerysetBuilder().within(prefix)
        queryset.organization(organization)
        queryset.net_type(["scope", "reserved"])
        return queryset.finalize()

    def list(self, request, *args, **kwargs):
        prefixes = self.get_queryset()
        prefix = self.request.QUERY_PARAMS.get("prefix", None)
        result = []
        if prefix is not None:
            base_prefix = prefix
            used_prefixes = map(addr, prefixes)
        else:
            base_prefix = map(addr, prefixes)
            used_prefixes = map(addr, get_within(prefixes))
        result = available_subnets(base_prefix, used_prefixes)
        # filter on size
        prefix_size = self.request.QUERY_PARAMS.get("prefix_size", None)
        if prefix_size is not None:
            prefix_size = int(prefix_size)
            result = [prefix for prefix in result if prefix.prefixlen() <= prefix_size]
        payload = {
            "available_subnets": map(lambda x: x.strNormal(), result)
        }
        return Response(payload, status=status.HTTP_200_OK)

def addr(prefix):
    return prefix.net_address

def get_within(prefixes):
    "Return all prefixes within 'prefixes'"
    acc = Prefix.objects.within(prefixes[0].net_address)
    for prefix in prefixes[1:]:
        _prefixes = Prefix.objects.within(prefix.net_address)
        acc = acc | _prefixes
    return acc

def available_subnets(base_prefixes, used_prefixes):
    if not isinstance(base_prefixes, list):
        base_prefixes = [base_prefixes]
    ips = IPSet([IP(prefix) for prefix in used_prefixes])
    acc = IPSet([IP(base_prefix) for base_prefix in base_prefixes])
    if not used_prefixes:
        return acc
    acc.discard(ips)
    # sanity check: only show subnets for IPv6 versions
    filtered = [ip for ip in acc if ip.version() == 4]
    # TODO: sort on length of subnets? (large subnets are more attractive?)
    return sorted(filtered, key=lambda x: -x.prefixlen())

router = routers.SimpleRouter()
router.register(r"^/find", PrefixFinderSet, base_name="ipam-api-finder")
router.register(r"^", PrefixViewSet, base_name="ipam-api")

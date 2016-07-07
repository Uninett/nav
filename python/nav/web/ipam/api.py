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


from rest_framework.response import Response
from rest_framework import viewsets, status, routers
from django.db.models import Q
import operator
import collections
from copy import copy
from IPy import IPSet, IP

from .prefix_tree import make_tree

from nav.models.manage import Prefix
from nav.web.api.v1.serializers import PrefixSerializer
from nav.web.api.v1.views import get_times

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

class PrefixViewSet(viewsets.ViewSet):
    serializer = PrefixSerializer
    search_fields = ("vlan__description")

    def get_queryset(self):
        types = self.request.QUERY_PARAMS.getlist("net_type", ["scope"])
        queryset = Prefix.objects.filter(vlan__net_type__in=types)
        # TODO: Do this in a way, way better way
        search = self.request.QUERY_PARAMS.get("search", None)
        if search is not None:
            search_params = [
                Q(vlan__description__icontains=search),
                Q(vlan__organization__id__icontains=search)
            ]
            queryset = queryset.filter(reduce(operator.or_, search_params))
        return queryset

    # TODO add serializer
    def list(self, request, *args, **kwargs):
        prefixes = self.get_queryset()
        # parse "?type=" args
        args = copy(DEFAULT_TREE_PARAMS)
        _types = self.request.QUERY_PARAMS.getlist("type", [])
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
        queryset = Prefix.objects.all()
        # filter to get scopes matching base IP address
        prefix = self.request.QUERY_PARAMS.get("prefix", None)
        if prefix is not None:
            queryset = Prefix.objects.within(prefix)
        # filter for organization. TODO this should really be done in the router
        organization = self.request.QUERY_PARAMS.get("organization", None)
        if organization is not None:
            queryset = queryset.filter(vlan__organization__id__icontains=organization)
        # only return scopes, reservations, TODO: maybe do this earlier on?
        queryset.filter(vlan__net_type__in=["scope", "reserved"])
        return queryset

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

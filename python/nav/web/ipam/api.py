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
from django.db.models import Q
from IPy import IPSet, IP

from .prefix_tree import make_tree

from nav.models.manage import Prefix
from nav.web.api.v1.serializers import PrefixSerializer
from nav.web.api.v1.views import get_times

from nav.web.api.v1.helpers import prefix_collector


from nav.web.ipam.util import PrefixQuerysetBuilder, get_available_subnets

class PrefixViewSet(viewsets.ViewSet):
    "Potpurri view for anything prefix related mostly"

    serializer = PrefixSerializer
    search_fields = ("vlan__description")

    def get_queryset(self):
        # Extract filters etc
        net_types = self.request.QUERY_PARAMS.getlist("net_type", ["scope"])
        search = self.request.QUERY_PARAMS.get("search", None)
        organization = self.request.QUERY_PARAMS.get("organization", None)
        vlan_number = self.request.QUERY_PARAMS.get("vlan", None)
        ip = self.request.QUERY_PARAMS.get("ip", None)
        within = self.request.QUERY_PARAMS.get("within", None)
        # Build queryset
        queryset = PrefixQuerysetBuilder()
        queryset.net_type(net_types)
        queryset.search(search)
        queryset.organization(organization)
        queryset.vlan_number(vlan_number)
        queryset.contains_ip(ip)
        queryset.within(within)
        return queryset.finalize()

    @detail_route(methods=["get"])
    def usage(self, request, *args, **kwargs):
        "Return usage for Prefix.pk == pk"
        pk = kwargs.pop("pk", None)
        # TODO: error handling
        prefix = Prefix.objects.get(pk=pk)
        max_addr = IP(prefix.net_address).len()
        active_addr = prefix_collector.collect_active_ip(prefix)
        # calculate allocated ratio
        allocated = PrefixQuerysetBuilder().within(prefix.net_address).finalize()
        allocated = allocated.exclude(vlan__net_type="scope")
        total_allocated = sum(p.get_prefix_size() for p in allocated)
        payload = {
            "max_addr": max_addr,
            "active_addr": active_addr,
            "usage": 1.0 * active_addr / max_addr,
            "allocated": 1.0 * total_allocated / max_addr,
            "pk": pk
        }
        return Response(payload, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        "List a tree-like structure of all prefixes matching the query"
        prefixes = self.get_queryset()
        family = self.request.QUERY_PARAMS.getlist("type", ["ipv4"])
        # create fake nodes to symbolize fake nodes
        show_available = self.request.QUERY_PARAMS.get("show_available", False)
        result = make_tree(prefixes, family=family, show_available=show_available)
        return Response(result.fields["children"], status=status.HTTP_200_OK)

class PrefixFinderSet(viewsets.ViewSet):
    "Utility view for finding available subnets"

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
        "List all available subnets for a given query"
        prefixes = self.get_queryset()
        prefix = self.request.QUERY_PARAMS.get("prefix", None)
        result = get_available_subnets(prefix, prefixes)
        # filter on size TODO error handling
        prefix_size = self.request.QUERY_PARAMS.get("prefix_size", None)
        if prefix_size is not None:
            prefix_size = int(prefix_size)
            result = [prefix for prefix in result if prefix.prefixlen() <= prefix_size]
        # breaking change TODO fix this in view code (assumes a map is returned)
        payload = [p.strNormal() for p in result]
        return Response(payload, status=status.HTTP_200_OK)

router = routers.SimpleRouter()
router.register(r"^/find", PrefixFinderSet, base_name="ipam-api-finder")
router.register(r"^", PrefixViewSet, base_name="ipam-api")

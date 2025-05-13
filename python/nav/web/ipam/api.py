# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from nav.ip import IP

from nav.models.manage import Prefix
from nav.web.api.v1.serializers import PrefixSerializer
from nav.web.api.v1.helpers import prefix_collector
from nav.web.ipam.util import (
    PrefixQuerysetBuilder,
    get_available_subnets,
    suggest_range,
)

from .prefix_tree import make_tree, make_tree_from_ip


# from nav.models.fields import CIDRField


# Inspired by
# http://blog.karolmajta.com/parsing-query-parameters-in-rest-framework/
class SuggestParams(serializers.Serializer):
    prefix = serializers.CharField()
    n = serializers.IntegerField(default=10)
    prefixlen = serializers.IntegerField(default=24, min_value=1, max_value=128)
    offset = serializers.IntegerField(default=0)

    def validate(self, data):
        try:
            if IP(data['prefix']).version() == 4 and data['prefixlen'] > 32:
                raise serializers.ValidationError(
                    "Prefixlen can not be higher than 32 for ipv4 prefixes"
                )
        except ValueError:
            raise serializers.ValidationError("Invalid prefix")
        return data


class PrefixViewSet(viewsets.ViewSet):
    """Potpurri view for anything IPAM needs to function properly.

    Filters
    -------
    - net_type: *Only return this type of prefix. Can be used multiple times.*
    - search: *Match against the description or organization of the VLAN*
    - ip: *Find all prefixes that contain this IP*
    - organization: *Match against the VLAN's organization*
    - vlan: *Match against a certain VLAN number*
    - description: *Match against the VLAN's description*
    - within: *Find all prefixes within this range*
    - usage: *Find all prefixes with this usage description*

    Examples
    --------
    ?net_type=scope&organization=NTNU&within=10.0.0.0/8

    """

    serializer = PrefixSerializer
    search_fields = "vlan__description"

    def get_queryset(self):
        "Build queryset for API using filters"
        net_types = self.request.query_params.getlist("net_type", None)
        if "all" in net_types:
            net_types = None
        search = self.request.query_params.get("search", None)
        if search is not None and search:
            net_types = None
        ip = self.request.query_params.get("ip", None)
        if ip is not None and ip:
            net_types = None
        organization = self.request.query_params.get("organization", None)
        vlan_number = self.request.query_params.get("vlan", None)
        description = self.request.query_params.get("description", None)
        within = self.request.query_params.get("within", None)
        usage = self.request.query_params.get("usage", None)
        # Build queryset
        queryset = PrefixQuerysetBuilder()
        queryset.within(within)
        queryset.net_type(net_types)
        queryset.search(search)
        queryset.organization(organization)
        queryset.vlan_number(vlan_number)
        queryset.contains_ip(ip)
        queryset.usage(usage)
        queryset.description(description)
        queryset.filter_full_prefixes()
        return queryset.finalize()

    @action(detail=False, methods=["get"])
    def suggest(self, request, *args, **kwargs):
        "Suggests subnets of size=?number_of_hosts for ?prefix"
        params = SuggestParams(data=request.query_params)
        if not params.is_valid():
            return Response(data=params.errors, status=status.HTTP_400_BAD_REQUEST)
        params = params.validated_data
        payload = suggest_range(
            params["prefix"],
            offset=params["offset"],
            prefixlen=params["prefixlen"],
            n=params["n"],
        )
        return Response(payload, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def usage(self, request, *args, **kwargs):
        "Return usage for Prefix.pk == pk"
        pk = kwargs.pop("pk", None)
        prefix = Prefix.objects.get(pk=pk)
        max_addr = IP(prefix.net_address).len()
        active_addr = prefix_collector.collect_active_ip(prefix)
        # calculate allocated ratio
        query = PrefixQuerysetBuilder().within(prefix.net_address)
        allocated = query.finalize().exclude(vlan__net_type="scope")
        total_allocated = sum(p.get_prefix_size() for p in allocated)
        payload = {
            "max_addr": max_addr,
            "active_addr": active_addr,
            "usage": 1.0 * active_addr / max_addr,
            "allocated": 1.0 * total_allocated / max_addr,
            "pk": pk,
        }
        return Response(payload, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        "List a tree-like structure of all prefixes matching the query"
        prefixes = self.get_queryset()
        family = self.request.query_params.getlist("type", ["ipv4", "ipv6", "rfc1918"])
        within = self.request.query_params.get("within", None)
        show_all = self.request.query_params.get("show_all", None)
        result = make_tree(prefixes, root_ip=within, family=family, show_all=show_all)
        payload = result.fields["children"]
        return Response(payload, status=status.HTTP_200_OK)


class PrefixFinderSet(viewsets.ViewSet):
    """Utility view for finding available subnets. Only returns prefixes that
    are either scopes or reserved.

    Filters
    -------
    - prefix: *Range or prefix to query against (e.g. '10.0.0.0/8')*
    - organization: *Match against the corresponding VLAN's organization*

    """

    serializer = PrefixSerializer

    def get_queryset(self):
        # Extract filters
        organization = self.request.query_params.get("organization", None)
        # Build queryset
        queryset = PrefixQuerysetBuilder()
        queryset.organization(organization)
        queryset.net_type(["scope", "reserved"])
        return queryset.finalize()

    def list(self, request, *args, **kwargs):
        """List all available subnets for the prefixes returned by the initial
        query.

        Filters
        -------
        - prefix: *Range or prefix to query against (e.g. '10.0.0.0/8')*
        - prefix_size: *The maximum prefix length (mask, e.g. /32)*

        """
        prefix = self.request.query_params.get("prefix", None)
        result = get_available_subnets(prefix)
        prefix_size = self.request.query_params.get("prefix_size", None)
        if prefix_size is not None:
            prefix_size = int(prefix_size)
            result = [prefix for prefix in result if prefix.prefixlen() <= prefix_size]
        payload = {
            "prefix": prefix,
            "prefixlen": prefix.split("/")[1],
            "children": make_tree_from_ip(result).fields["children"],
        }
        return Response(payload, status=status.HTTP_200_OK)


router = routers.SimpleRouter()
router.register(r"^/find", PrefixFinderSet, basename="ipam-api-finder")
router.register(r"^", PrefixViewSet, basename="ipam-api")

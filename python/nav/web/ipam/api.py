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
from copy import copy

from .prefix_tree import make_tree

from nav.models.manage import Prefix
from nav.web.api.v1.serializers import PrefixSerializer

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
        types = ["scope", "reserved"]
        # types = ["scope"]
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
        result = make_tree(prefixes, **args)
        return Response(result.fields["children"], status=status.HTTP_200_OK)

router = routers.SimpleRouter()
router.register(r"^", PrefixViewSet, base_name="ipam-api")

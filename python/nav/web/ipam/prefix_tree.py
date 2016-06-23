# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2016 UNINETT AS
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

from __future__ import unicode_literals
from IPy import IP
from collections import namedtuple
from django.utils.encoding import smart_str, smart_unicode
import json

from nav.models.manage import Vlan, Prefix

# this is hilariously expensive
def get_prefixes():
    types = ["scope"]
    return Prefix.objects.filter(vlan__net_type__in=types)
    return acc

## prefix code

# To maintain our sanity, we need a somewhat decent contract between the view
# and any controller logic. The solution is to use the Facade pattern, which
# wraps internal complexities (serialization, nested attributes and so on) and
# exposes a clean, non-nested attribute contract (we promise that the field 'x'
# will exist) etc.

class JsonFacade(object):
    """Simple Facade pattern utility for serializing to JSON. obj.json_fields is a
list of the class attributes which you wish to serialize.

    """

    @property
    def json(self):
        """Serialize (a subset of) the node. Iterates over the attributes specifies in
        self.json_fields and adds them to a JSON map

        """
        payload = {}
        for field in self.JSON_FIELDS:
            value = getattr(self, field, None)
            payload[field] = value if value else None
        return json.dumps(payload)

class IpNodeFacade(JsonFacade):
    "Utility mixin for nodes with IPy.IP objects in in the 'self.ip' field"

    JSON_FIELDS = ["pk", "length", "net_type", "cidr", "children_pks"]

    @property
    def cidr(self):
        return str(self.ip)

    @property
    def children_pks(self):
        if not self.children:
            return []
        return [child.pk for child in self.children]

    @property
    def length(self):
        "Return number of children (in total, e.g. not shallow)"
        total = 0
        for child in self.children:
            total += child.children_count
        return total + self.children_count

    # Comparison utilities

    def __contains__(self, other):
        assert isinstance(other, PrefixHeap), "Can only compare with other PrefixHeap elements"
        return other.ip in self.ip

    def __cmp__(self, other):
        assert isinstance(other, PrefixHeap), "Can only compare with other PrefixHeap elements"
        return self.ip.__cmp__(other.ip)

class PrefixHeap(JsonFacade):
    def __init__(self, children=None):
        if children is None:
            children = []
        self.children = children

    @property
    def children_count(self):
        "Return number of children (shallow)"
        return len(self.children)

    def add(self, node):
        assert isinstance(node, PrefixHeap), "Can only add classes inheriting from PrefixHeap"
        # first, try adding to children (recursively)
        matches = (child for child in self.children if node in child)
        for child in matches:
            child.add(node)
            return
        # if this fails, add to self
        self.children.append(node)
        self.children.sort()

class FauxNode(PrefixHeap, IpNodeFacade):
    def __init__(self, ip_addr, pk, net_type):
        self.children = []
        self.ip = IP(ip_addr)
        self.pk = pk
        self.net_type = net_type

    @property
    def is_fake(self):
        return True

class PrefixNode(PrefixHeap, IpNodeFacade):
    def __init__(self, prefix):
        self.children = []
        self.net_type = str(prefix.vlan.net_type)
        self.pk = prefix.pk
        self.ip = IP(prefix.net_address)
        self.description = prefix.vlan.description
        self.organization = prefix.vlan.organization

def make_prefix_heap(initial_children=None):
    "Return a prefix heap of all prefixes"
    heap = PrefixHeap(initial_children)
    nodes = [PrefixNode(prefix) for prefix in get_prefixes()]
    for node in sorted(nodes, reverse=True):
        heap.add(node)
    return heap

# TODO: Generate three groups of scopes: RFC1918, IPv4 and IPv6
def make_tree():
    rfc_1918 = [
        FauxNode("10.0.0.0/8", "rfc1918-a", "RFC1918"),
        FauxNode("172.16.0.0/12", "rfc1918-b", "RFC1918"),
        FauxNode("192.168.0.0/16", "rfc1918-c", "RFC1918")
    ]
    return make_prefix_heap(rfc_1918)



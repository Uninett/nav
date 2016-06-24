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
#

from __future__ import unicode_literals
from IPy import IP
import json

from nav.models.manage import Prefix

# this is hilariously expensive
def get_prefixes():
    "Return all prefixes found in NAV (just scopes for now)"
    types = ["scope"]
    return Prefix.objects.filter(vlan__net_type__in=types)

## prefix code

# To maintain our sanity, we need a somewhat decent contract between the view
# and any controller logic. The solution is to use the Facade pattern, which
# wraps internal complexities (serialization, nested attributes and so on) and
# exposes a clean, non-nested attribute contract (we promise that the field 'x'
# will exist) etc.

class PrefixHeap(object):
    "Pseudo-heap ordered topologically by prefixes"
    def __init__(self, children=None):
        if children is None:
            children = []
        self.children = children

    @property
    def children_count(self):
        "Return number of children (shallow)"
        return len(self.children)

    def add(self, node):
        "Add a node to the heap"
        assert isinstance(node, PrefixHeap), \
            "Can only add classes inheriting from PrefixHeap"
        # first, try adding to children (recursively)
        matches = (child for child in self.children if node in child)
        for child in matches:
            child.add(node)
            return
        # if this fails, add to self
        self.children.append(node)
        self.children.sort()

class IpNodeFacade(PrefixHeap):
    "Utility mixin for nodes with IPy.IP objects in in the 'self.ip' field"

    # Class attributes to export to JSON
    JSON_FIELDS = [
        "pk",
        "length",
        "net_type",
        "cidr",
        "children_pks",
        "ip_version",
        "prefixlen"
    ]

    def __init__(self, ip_addr, pk, net_type):
        super(IpNodeFacade, self).__init__()
        self.ip = IP(ip_addr)
        self.pk = pk
        self.net_type = net_type

    @property
    def json(self):
        "Serialize (a subset of) the node. See JSON_FIELDS"
        payload = {}
        for field in self.JSON_FIELDS:
            try:
                value = getattr(self, field, None)
                payload[field] = value if value else None
            except AttributeError:
                payload[field] = None
        return json.dumps(payload)

    @property
    def ip_version(self):
        "Return the IP family of this prefix (4 or 6)"
        return self.ip.version()

    @property
    def prefixlen(self):
        "Return the length of the prefix (e.g. 8 in 10.0.0.0/8)"
        return self.ip.prefixlen()

    @property
    def cidr(self):
        "Return the prefix (as a string)"
        return str(self.ip)

    @property
    def children_pks(self):
        "Return the primary keys of all children"
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
        assert isinstance(other, PrefixHeap), \
            "Can only compare with other PrefixHeap elements"
        return other.ip in self.ip

    def __cmp__(self, other):
        assert isinstance(other, PrefixHeap), \
            "Can only compare with other PrefixHeap elements"
        return self.ip.__cmp__(other.ip)

class FauxNode(IpNodeFacade):
    "'Fake' nodes (manual constructor) in a prefix heap"
    def __init__(self, ip_addr, pk, net_type):
        super(FauxNode, self).__init__(ip_addr, pk, net_type)

    @property
    def is_fake(self):
        "Marker propery for declaring the node as fake (templating reasons)"
        return True

class PrefixNode(IpNodeFacade):
    "Wrapper node for Prefix results"
    def __init__(self, prefix):
        ip_addr = prefix.net_address
        pk = prefix.pk
        net_type = str(prefix.vlan.net_type)
        super(PrefixNode, self).__init__(ip_addr, pk, net_type)
        self.description = prefix.vlan.description
        self.organization = prefix.vlan.organization

def make_prefix_heap(initial_children=None):
    "Return a prefix heap of all prefixes"
    heap = PrefixHeap(initial_children)
    nodes = [PrefixNode(prefix) for prefix in get_prefixes()]
    for node in sorted(nodes, reverse=True):
        heap.add(node)
    return heap

def make_tree():
    "Return a prefix heap initially populated with RFC1918 addresses"
    rfc_1918 = [
        FauxNode("10.0.0.0/8", "rfc1918-a", "RFC1918"),
        FauxNode("172.16.0.0/12", "rfc1918-b", "RFC1918"),
        FauxNode("192.168.0.0/16", "rfc1918-c", "RFC1918")
    ]
    return make_prefix_heap(rfc_1918)



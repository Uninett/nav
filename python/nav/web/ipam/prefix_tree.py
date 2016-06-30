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
import copy

from django.core.urlresolvers import reverse, NoReverseMatch
from nav.models.manage import Prefix

# this is hilariously expensive
def get_prefixes():
    "Return all prefixes found in NAV (just scopes for now)"
    types = ["scope"]
    return Prefix.objects.filter(vlan__net_type__in=types)

## Prefix code

# To maintain our sanity, we need a somewhat decent contract between the view
# and any controller logic. The solution is to use the Facade pattern, which
# wraps internal complexities (serialization, nested attributes and so on) and
# exposes a clean, non-nested attribute contract (we promise that the field 'x'
# will exist and be populated with some value) etc.

class PrefixHeap(object):
    "Pseudo-heap ordered topologically by prefixes"
    def __init__(self, children=None):
        if children is None:
            children = []
        self.children = children

    @property
    def fields(self):
        payload = {
            "children": [child.fields for child in self.children]
        }
        return payload

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def json_walk(self):
        "JSON output of self.walk"
        return json.dumps(self.walk)

    @property
    def walk(self):
        "List of all the nodes (preorder walk)."
        acc = []
        q = [self]
        while q:
            _node = q.pop()
            # remove children to avoid duplication
            node = copy.deepcopy(_node.fields)
            del node["children"]
            acc.append(node)
            if not _node.is_leaf:
                q.extend(_node.children)
        return acc

    @property
    def json(self):
        return json.dumps(self.fields)

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
    FIELDS = [
        "pk",
        "length",
        "net_type",
        "children_pks",
        "ip_version",
        "edit_url",
        "prefix",
        "prefixlen",
        "organization",
        "description"
    ]

    def __init__(self, ip_addr, pk, net_type):
        super(IpNodeFacade, self).__init__()
        self.ip = IP(ip_addr)
        self.pk = pk
        self.net_type = net_type

    @property
    def fields(self):
        payload = {}
        for field in self.FIELDS:
            try:
                value = getattr(self, field, None)
                payload[field] = value if value else None
            except AttributeError:
                payload[field] = None
        payload["children"] = [child.fields for child in self.children]
        return payload

    @property
    def ip_version(self):
        "Return the IP family of this prefix (4 or 6)"
        return self.ip.version()

    @property
    def edit_url(self):
        try:
            return reverse("seeddb-prefix-edit", kwargs={"prefix_id": self.pk})
        except NoReverseMatch:
            return None

    @property
    def prefixlen(self):
        "Return the length of the prefix (e.g. 8 in 10.0.0.0/8)"
        return self.ip.prefixlen()

    @property
    def prefix(self):
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
        deep_count = sum(child.children_count for child in self.children)
        return self.children_count + deep_count

    @property
    def organization(self):
        return str(getattr(self, "_organization", ""))

    @property
    def description(self):
        return getattr(self, "_description", "")

    @property
    def is_mock_node(self):
        "Marker propery for declaring the node as fake (templating reasons)"
        return False

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
    def is_mock_node(self):
        "Marker propery for declaring the node as fake (templating reasons)"
        return True

class PrefixNode(IpNodeFacade):
    "Wrapper node for Prefix results"
    def __init__(self, prefix):
        ip_addr = prefix.net_address
        pk = prefix.pk
        net_type = str(prefix.vlan.net_type)
        super(PrefixNode, self).__init__(ip_addr, pk, net_type)
        self._description = prefix.vlan.description
        self._organization = prefix.vlan.organization

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



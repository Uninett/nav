# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Uninett AS
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
Utility class for creating prefix heaps from Prefix objects in NAV. Also
contains ad-hoc serializer methods (self.fields) for API purposes.

"""

import bisect
import json
import functools
import logging
from IPy import IP, IPSet

from django.urls import reverse, NoReverseMatch

from nav.web.ipam.util import get_available_subnets
from nav.models.manage import Prefix


_logger = logging.getLogger(__name__)


class PrefixHeap(object):
    "Pseudo-heap ordered topologically by prefixes"

    def __init__(self, children=None):
        if children is None:
            children = []
        self.children = children

    @property
    def fields(self):
        "Return the children of the heap as a dictionary"
        payload = {"children": [child.fields for child in self.children]}
        return payload

    def is_leaf(self):
        "Whether or not the node has any children"
        return len(self.children) == 0

    def walk(self):
        "List of all the nodes (preorder walk)."
        queue = []
        queue.extend(self.children)
        while queue:
            _node = queue.pop()
            if not _node:
                continue
            queue.extend(_node.children)
            yield _node

    def walk_roots(self):
        "Walk non-leaf nodes in heap (preorder)"
        for node in self.walk():
            if not node.is_leaf():
                yield node

    @property
    def json(self):
        "Exported fields as a JSON map"
        return json.dumps(self.fields)

    @property
    def children_count(self):
        "Number of children (shallow)"
        return len(self.children)

    def add(self, node):
        "Add a node to the heap"
        assert isinstance(node, PrefixHeap), (
            "Can only add classes inheriting from PrefixHeap"
        )
        # first, try adding to children (recursively)
        i = bisect.bisect_left(self.children, node)
        if i > 0 and node in self.children[i - 1]:
            child = self.children[i - 1]
            node.parent = child
            child.add(node)
            return
        self.children.insert(i, node)

    def add_many(self, nodes):
        "Add multiple nodes to heap"
        for node in nodes:
            self.add(node)


# To maintain our sanity, we need a somewhat decent contract between the view
# and any controller logic. The solution is to use the Facade pattern, which
# wraps internal complexities (serialization, nested attributes and so on) and
# exposes a clean, non-nested attribute contract (we promise that the field 'x'
# will exist and be populated with some value) etc.


@functools.total_ordering
class IpNode(PrefixHeap):
    "PrefixHeap node class"

    def __init__(self, ip_addr, net_type):
        super(IpNode, self).__init__()
        self._ip = IP(ip_addr)
        self.net_type = net_type

    @property
    def ip(self):
        "Return the IP object of the node"
        return self._ip

    def not_in_use(self):
        "Show unused subnets in the CIDR range"
        if self.is_leaf() or self.net_type != "scope":
            return []
        base_set = IPSet([self.ip])
        for child in self.children:
            base_set.discard(child.ip)
        return base_set.prefixes

    def in_use(self):
        "Show allocated *used( subnets in the CIDR range"
        return IPSet([child.ip for child in self.children])

    # Comparison utilities
    def __contains__(self, other):
        assert isinstance(other, IpNode), "Can only compare with other IpNode elements"
        return other.ip in self.ip

    def __cmp__(self, other):
        assert isinstance(other, IpNode), "Can only compare with other IpNode elements"
        return self.ip.__cmp__(other.ip)

    def __eq__(self, other):
        assert isinstance(other, IpNode), "Can only compare with other IpNode elements"
        return self.ip == other.ip

    def __lt__(self, other):
        assert isinstance(other, IpNode), "Can only compare with other IpNode elements"
        return self.ip < other.ip


class IpNodeFacade(IpNode):
    "Utility mixin for nodes with IPy.IP objects in in the 'self.ip' field"

    # Class attributes to export to JSON
    FIELDS = [
        "pk",
        "length",
        "net_type",
        "children_pks",
        "net_ident",
        "ip_version",
        "edit_url",
        "prefix",
        "prefixlen",
        "organization",
        "description",
        "vlan_number",
        "is_mock_node",
        "last_octet",
        "bits",
        "empty_ranges",
        "is_reservable",
        "parent_pk",
    ]

    def __init__(self, ip_addr, pk, net_type, sort_fn=None):
        super(IpNodeFacade, self).__init__(ip_addr, net_type)
        self.pk = pk
        self.sort_fn = sort_fn

    @property
    def parent_pk(self):
        "The primary key of the node's parent"
        if self.parent is None:
            return None
        return self.parent.pk

    @property
    def is_reservable(self):
        "Whether or not the prefix can be reserved in NAV"
        empty_scope = self.net_type == "scope" and self.length == 0
        return self.net_type == "available" or empty_scope

    @property
    def empty_ranges(self):
        "Ranges within the node not spanned by its children"
        return [str(prefix) for prefix in self.not_in_use()]

    @property
    def net_ident(self):
        "The identity of the associated VLAN/network"
        ident = getattr(self, "_net_ident", None)
        return ident if ident else None

    @property
    def bits(self):
        "Numeric value of address"
        return self.ip.ip

    @property
    def fields(self):
        """Return all fields marked for serialization (in self.FIELDS) as a
        Python dict. Also serializes children, creating a nested object.

        """
        payload = {}
        for field in self.FIELDS:
            try:
                value = getattr(self, field, None)
                payload[field] = value
            except AttributeError:
                payload[field] = None
        if self.sort_fn is not None:
            children = [child.fields for child in self.children]
            payload["children"] = sorted(children, key=self.sort_fn)
        else:
            payload["children"] = [child.fields for child in self.children]
        return payload

    @property
    def last_octet(self):
        "Return last octet of address"
        return self.ip.ip & 0xFF

    @property
    def vlan_number(self):
        "Return ID number of associated VLAN"
        return getattr(self, "_vlan_number", None)

    @property
    def ip_version(self):
        "Return the IP family of this prefix (4 or 6)"
        return self.ip.version()

    @property
    def edit_url(self):
        "URL to edit this node in SeedDB, if applicable"
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
        "The name of the organization connected to the prefix"
        return str(getattr(self, "_organization", ""))

    @property
    def description(self):
        "The description of the prefix"
        return getattr(self, "_description", "")

    @property
    def is_mock_node(self):
        "Marker property for declaring the node as fake (templating reasons)"
        return False


class FauxNode(IpNodeFacade):
    "'Fake' nodes (manual constructor) in a prefix heap"

    def __init__(self, ip_addr, pk, net_type):
        super(FauxNode, self).__init__(ip_addr, pk, net_type)

    @property
    def is_mock_node(self):
        "Marker propery for declaring the node as fake (templating reasons)"
        return True


class FakeVLAN(object):
    "Mock object that quacks like prefix.vlan"

    def __init__(self):
        pass

    @property
    def net_type(self):
        "The type of the network"
        return "UNKNOWN"

    @property
    def description(self):
        "Description of the network"
        return "UNKNOWN"

    @property
    def organization(self):
        "Organization connected to the network"
        return "UNKNOWN"

    @property
    def vlan(self):
        "The VLAN ID of the network"
        return "UNKNOWN"

    @property
    def net_ident(self):
        "The network identifier of the network"
        return "UNKNOWN"


class PrefixNode(IpNodeFacade):
    "Wrapper node for Prefix results"

    def __init__(self, prefix, sort_fn=None):
        self._prefix = prefix  # cache of prefix
        ip_addr = prefix.net_address
        primary_key = prefix.pk
        # Some prefixes might not have an associated VLAN due to data/migration
        # issues, in which case we use a filler
        vlan = getattr(prefix, "vlan", None)
        if vlan is None:
            _logger.warning(
                "Prefix % id=% does not have a VLAN relation",
                prefix.net_address,
                prefix.id,
            )
            vlan = FakeVLAN()
        net_type = str(vlan.net_type)
        super(PrefixNode, self).__init__(ip_addr, primary_key, net_type, sort_fn)
        self._description = vlan.description
        self._organization = vlan.organization
        self._vlan_number = vlan.vlan
        self._net_ident = vlan.net_ident
        # Export usage field of VLAN
        if getattr(vlan, "usage", None):
            self.vlan_usage = prefix.vlan.usage.description
            self.FIELDS.append("vlan_usage")


def make_prefix_heap(
    prefixes,
    initial_children=None,
    family=None,
    sort_fn=None,
    show_available=False,
    show_unused=False,
):
    """Return a prefix heap of all prefixes. Might optionally filter out IPv4
    and IPv6 as needed.

    Args:
        prefixes: a queryset for or list of nav.models.manage.Prefix
        initial_children: a list of IPNode to initialize the root with
        family: a list of address types to allow (of "ipv4", "ipv6", "rfc1918")
        sort_fn: function used to sort the children upon serialization
        show_available: whether or not to create "fake" children for all ranges
            not spanned by the node's children or found otherwhere in NAV
        show_unused: like above, but only creates such nodes for prefixes that
            are in fact found within NAV

    Returns:
        A prefix heap (tree)

    """
    rfc1918 = IPSet([IP("10.0.0.0/8"), IP("172.16.0.0/12"), IP("192.168.0.0/16")])

    def accept(prefix):
        "Helper function for filtering prefixes by IP family"
        ip_addr = IP(prefix.net_address)
        if "ipv4" in family and ip_addr.version() == 4 and ip_addr not in rfc1918:
            return True
        if "ipv6" in family and ip_addr.version() == 6:
            return True
        if "rfc1918" in family and ip_addr in rfc1918:
            return True
        return False

    heap = PrefixHeap(initial_children)
    filtered = (prefix for prefix in prefixes if accept(prefix))
    nodes = (PrefixNode(prefix, sort_fn=sort_fn) for prefix in filtered)
    for node in sorted(nodes, reverse=False):
        heap.add(node)
    # Add marker nodes for available ranges/prefixes
    if show_available:
        scopes = (child for child in heap.walk_roots() if child.net_type in ["scope"])
        subnets = (get_available_nodes([scope.ip]) for scope in scopes)
        for subnet in subnets:
            heap.add_many(subnet)
    # Add marker nodes for empty ranges, e.g. ranges not spanned by the
    # children of a node. This is useful for aligning visualizations and so on.
    if show_unused:
        unused_prefixes = (child.not_in_use() for child in heap.walk())
        for unused_prefix in unused_prefixes:
            nodes = nodes_from_ips(unused_prefix, klass="empty")
            heap.add_many(nodes)
    return heap


SORT_BY = {"vlan_number": lambda x: x.vlan_number}


def get_available_nodes(ips):
    """Find available subnets for each IP in 'ips' and return them as
    FauxNodes.

    """
    available_nodes = get_available_subnets(ips)
    return nodes_from_ips(available_nodes, klass="available")


def nodes_from_ips(ips, klass="empty"):
    "Turn a list of IPs into FauxNodes"
    return [FauxNode(ip, ip.strNormal(), klass) for ip in ips]


def make_tree(prefixes, family=None, root_ip=None, show_all=None, sort_by="ip"):
    """Return a prefix heap initially populated with RFC1918 addresses. Accepts
    parameters rfc1918, ipv4 and ipv6 to return addresses of those respective
    families. Do note that we distinguish between 'real' IPv4, which is everything
    not part of the RFC1918 ranges.

        Args:
            prefixes: a queryset for or list of nav.models.manage.Prefix
            family: a list of address types to allow (of "ipv4", "ipv6", "rfc1918")
            root_ip: prefix string or IPy.IP object to use as the root of the tree
            show_all: whether or not to create fake nodes that fill in available
                within a parent (e.g. unused subnets) or nodes that are detected
                within this prefix for NAV, but still not present in the heap
            sort_by: key to sort the nodes/children by

        Returns:
            A prefix heap (tree)

    """
    family = {"ipv4", "ipv6", "rfc1918"} if family is None else set(family)
    init = []

    if root_ip is not None and root_ip:
        try:
            scope = Prefix.objects.get(net_address=root_ip)
            node = PrefixNode(scope)
        except Prefix.DoesNotExist:
            node = FauxNode(root_ip, "scope", "scope")
        init.append(node)

    opts = {
        "initial_children": init,
        "family": family,
        "sort_fn": SORT_BY.get(sort_by, None),
        "show_available": show_all,
        "show_unused": show_all,
    }
    return make_prefix_heap(prefixes, **opts)


def make_tree_from_ip(cidr_addresses):
    """Like make_tree, but for strings of CIDR addresses

    Args:
        cidr_addresses: A list of strings of prefixes ("10.0.0.0/8")

    Returns:
        A prefix heap (or tree).

    """
    heap = PrefixHeap()
    for addr in cidr_addresses:
        prefix = FauxNode(addr, "available", "available")
        heap.add(prefix)
    return heap

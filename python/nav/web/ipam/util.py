from nav.models.manage import Prefix
from django.db.models import Q
from IPy import IP, IPSet
from itertools import islice
import math

# Utility class (builder pattern) to get the Prefixes we want. Returns the
# resulting queryset when 'finalize' is called.
class PrefixQuerysetBuilder(object):
    "Utility class to build queryset(s) for Prefix"

    def __init__(self, queryset=None):
        if queryset is None:
            queryset = Prefix.objects.all()
        self.queryset = queryset
        self.is_realized = False

    def filter(self, origin, *args, **kwargs):
        """Works like queryset.filter, but returns self and short-circuits on
        'None' origin

        """
        if origin is not None:
            self.queryset = self.queryset.filter(*args, **kwargs)
        return self

    def finalize(self):
        "Returns the queryset with all filters applied"
        return self.queryset

    # Filter methods
    def organization(self, org):
        "Fuzzy match prefix on VLAN organization"
        return self.filter(org, vlan__organization__id__icontains=org)

    def description(self, descr):
        "Fuzzy match prefix on VLAN description"
        return self.filter(descr, vlan__description__icontains=descr)

    def vlan_number(self, vlan_number):
        "Return prefixes belonging to a particular VLAN"
        return self.filter(vlan_number, vlan__vlan=vlan_number)

    def net_type(self, net_type_or_net_types):
        "Return prefixes only of the given type(s)"
        if net_type_or_net_types is None:
            return self
        types = net_type_or_net_types
        if not isinstance(types, list):
            types = [types]
        return self.filter(types, vlan__net_type__in=types)

    def search(self, query):
        """Fuzzy search prefixes with query on VLAN description or
        organization

        """
        q = Q()
        q.add(Q(vlan__description__icontains=query), Q.OR)
        q.add(Q(vlan__organization__id__icontains=query), Q.OR)
        return self.filter(query, q)

    # Mutating methods, e.g. resets the queryset
    def within(self, prefix):
        "Sets the queryset to every Prefix within a certain prefix"
        if prefix is None:
            return self
        self.queryset = self.queryset & Prefix.objects.within(prefix)
        return self

    def contains_ip(self, addr):
        "Returns all prefixes containing the given address"
        if addr is None:
            return self
        self.queryset = self.queryset & Prefix.objects.contains_ip(addr)
        return self

# Code finding available subnets
def get_available_subnets(prefix_or_prefixes):
    """Get available prefixes within a list of CIDR addresses. Returns an
    iterable IPSet of available addresses.

    """
    if not isinstance(prefix_or_prefixes, list):
        prefix_or_prefixes = [prefix_or_prefixes]
    base_prefixes = [str(prefix) for prefix in prefix_or_prefixes]
    # prefixes we are scoping our subnet search to
    base = IPSet()
    # prefixes in use
    acc = IPSet()
    for prefix in base_prefixes:
        base.add(IP(prefix))
        used_prefixes = PrefixQuerysetBuilder().within(prefix).finalize()
        for used_prefix in used_prefixes:
            acc.add(IP(used_prefix.net_address))
    # remove used prefixes
    base.discard(acc)
    # filter away original prefixes
    return sorted([ip for ip in base if str(ip) not in base_prefixes])

def partition_subnet(n, prefix):
    "Partition prefix into subnets with room for at at least n hosts"
    subnet_size = math.ceil(math.log(n, 2))
    chunk_size = 2 ** subnet_size
    _iter = iter(IP(prefix))
    chunk = list(islice(_iter, chunk_size))
    while chunk:
        yield IPSet(chunk).prefixes[0]
        chunk = list(islice(_iter, chunk_size))

def suggest_range(prefix, number_of_hosts):
    """Partitions prefix into blocks of 'n' hosts. Returns a list of
    [startAddr, endAddr, prefix]

    """
    blocks = partition_subnet(number_of_hosts, prefix)
    acc = {
        "prefix": prefix,
        "requested_size": number_of_hosts,
        "candidates": []
    }
    for block in blocks:
        acc["candidates"].append({
            "length": block.len(),
            "prefix": str(block),
            "start": str(block[-0]),
            "end": str(block[-1])
        })
    return acc

from nav.models.manage import Prefix
from django.db.models import Q
from IPy import IP, IPSet


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

def get_available_subnets(prefix):
    pass

def get_available_subnets(base_prefix, other_prefixes):
    """Return all available subnets within base_prefixes, or if its not given,
    returns the available subnets within other_prefixes.

    """
    addr = lambda x: x.net_address
    base, rest = base_prefix, get_addresses(other_prefixes)
    if base_prefix is None:
        within = get_within(other_prefixes)
        base, rest = rest, get_addresses(within)
    return available_subnets(base, rest)

def get_addresses(prefixes):
    "Return addresses of multiple prefixes"
    return [prefix.net_address for prefix in prefixes]

def get_within(prefixes):
    "Return all prefixes within 'prefixes'"
    acc = Prefix.objects.within(prefixes[0].net_address)
    for prefix in prefixes[1:]:
        _prefixes = Prefix.objects.within(prefix.net_address)
        acc = acc | _prefixes
    return acc

def available_subnets(base_prefixes, used_prefixes):
    "Subtracts the netmasks of used_prefixes from base_prefixes"
    if not isinstance(base_prefixes, list):
        base_prefixes = [base_prefixes]
    ips = IPSet([IP(prefix) for prefix in used_prefixes])
    acc = IPSet([IP(base_prefix) for base_prefix in base_prefixes])
    if not used_prefixes:
        return acc
    acc.discard(ips)
    # sanity check: only show subnets for IPv6 versions
    filtered = [ip for ip in acc if ip.version() == 4]
    return sorted(filtered, key=lambda x: -x.prefixlen())

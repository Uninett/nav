from collections import defaultdict
from typing import Any
import logging

from django.core.cache import cache
import IPy

from nav.dhcpstats.common import DhcpPath
from nav.metrics.graphs import (
    aliased_series,
    json_graph_url,
    nonempty_series,
    summed_series,
)
from nav.metrics.names import get_expanded_nodes, safe_name
from nav.metrics.templates import metric_path_for_dhcp


_logger = logging.getLogger(__name__)


DHCP_PATHS_CACHE_KEY = "dhcpstats:graphite_paths"
DHCP_PATHS_CACHE_DURATION = 3600


def fetch_graph_urls_for_prefixes(prefixes: list[IPy.IP]) -> list[str]:
    """
    Takes a list of IP prefixes, queries Graphite for DHCP stat paths, and
    returns a list of Graphite graph URLs; one URL for each group of DHCP stat
    paths in Graphite where at least one path in the group represents a range of
    IP addresses that intersect with one or more of the given prefixes.

    Each returned Graphite URL points to JSON graph data and can be supplied
    directly to NAV's JavaScript RickshawGraph function.
    """
    if not prefixes:
        return []

    all_paths = fetch_paths_from_graphite()
    grouped_paths = group_paths(all_paths)
    filtered_grouped_paths = drop_groups_not_in_prefixes(grouped_paths, prefixes)

    graph_urls: list[str] = []
    for paths_of_same_group in sorted(filtered_grouped_paths):
        paths_of_same_group = sorted(paths_of_same_group)
        graph_lines = []
        for path in paths_of_same_group:
            assigned_addresses = nonempty_series(
                aliased_series(
                    path.to_graphite_path("assigned"),
                    name=(
                        f"Assigned addresses in {path.allocation_type} "
                        f"{range_str(path.first_ip, path.last_ip)}"
                    ),
                    renderer="area",
                ),
            )
            graph_lines.append(assigned_addresses)

        # Just select an arbitrary path instance in the group
        if len(paths_of_same_group) == 0:
            _logger.error("group_paths() returned an empty group")
            continue
        path = paths_of_same_group[0]

        unassigned_addresses = aliased_series(
            summed_series(path.to_graphite_path("unassigned", wildcard_for_group=True)),
            name="Total unassigned addresses",
            renderer="area",
            color="#d9d9d9",
        )
        graph_lines.append(unassigned_addresses)
        total_addresses = aliased_series(
            summed_series(path.to_graphite_path("total", wildcard_for_group=True)),
            name="Total addresses",
            color="#707070",
        )
        graph_lines.append(total_addresses)

        type_human = path.allocation_type + ("" if path.is_standalone() else "s")
        title = (
            f"{path.group_name} {type_human} on DHCPv{path.ip_version} server "
            f"'{path.server_name}'"
        )
        graph_urls.append(json_graph_url(*graph_lines, title=title))
    return graph_urls


def fetch_paths_from_graphite():
    """
    Fetches and returns all unique DHCP stat paths in Graphite when their
    trailing metric_name path segment has been removed.
    """
    return cache.get_or_set(
        DHCP_PATHS_CACHE_KEY,
        _fetch_paths_from_graphite,
        timeout=DHCP_PATHS_CACHE_DURATION,
    )


def _fetch_paths_from_graphite():
    """Actual implementation of fetch_paths_from_graphite()"""
    wildcard = metric_path_for_dhcp(
        ip_version=safe_name("{4,6}"),
        server_name=safe_name("*"),
        allocation_type=safe_name("{range,pool,subnet}"),
        group_name_source=safe_name("{custom_groups,special_groups}"),
        group_name=safe_name("*"),
        first_ip=safe_name("*"),
        last_ip=safe_name("*"),
        metric_name="assigned",
    )
    graphite_paths = get_expanded_nodes(wildcard)

    native_paths: list[DhcpPath] = []
    for graphite_path in graphite_paths:
        try:
            native_path = DhcpPath.from_graphite_path(graphite_path)
        except ValueError as err:
            _logger.warning(
                "Could not decode the timeseries path '%s' fetched from Graphite: %s. "
                "NAV will ignore this path, whereas Graphite will not; this incorrect "
                "Graphite state is a likely cause of graphing-related bugs.",
                graphite_path,
                err,
            )
            pass
        else:
            native_paths.append(native_path)
    return native_paths


def group_paths(paths: list[DhcpPath]):
    """
    Takes a list of DhcpPath instances and partitions it into multiple lists,
    such that two DhcpPath instances belong to the same list if and only if they
    have the same group data.
    """
    grouped_paths: dict[Any, list[DhcpPath]] = defaultdict(list)
    for path in paths:
        group_path = path.to_graphite_path("assigned", wildcard_for_group=True)
        grouped_paths[group_path].append(path)
    return list(grouped_paths.values())


def drop_groups_not_in_prefixes(
    grouped_paths: list[list[DhcpPath]], prefixes: list[IPy.IP]
):
    """
    Takes a list of grouped DhcpPath instances, and returns only the groups that
    have at least one DhcpPath instance that intersect with one or more of the
    given prefixes.
    """
    grouped_paths_to_keep: list[list[DhcpPath]] = []
    for paths_of_same_group in grouped_paths:
        if any(path.intersects(prefixes) for path in paths_of_same_group):
            grouped_paths_to_keep.append(paths_of_same_group)
    return grouped_paths_to_keep


def range_str(first_ip: IPy.IP, last_ip: IPy.IP):
    """
    Returns a human-readable string that represents the range of IP addresses
    between first_ip and last_ip (inclusive). If the addresses comprise a CIDR
    block, CIDR notation is used. Otherwise, an ad-hoc notation is used.

    >>> range_str(IPy.IP("192.0.0.32"), IPy.IP("192.0.0.63"))
    "192.0.0.32/27"
    >>> range_str(IPy.IP("192.0.0.31"), IPy.IP("192.0.0.63"))
    "192.0.0.31-192.0.0.63"
    >>> range_str(IPy.IP("192.0.0.32"), IPy.IP("192.0.0.64"))
    "192.0.0.32-192.0.0.64"
    """
    fallback = f"{first_ip}-{last_ip}"
    if first_ip.version() == last_ip.version() == 4:
        totalbits = 32
    elif first_ip.version() == last_ip.version() == 6:
        totalbits = 128
    else:
        return fallback
    hostbits = (last_ip.int() - first_ip.int()).bit_length()
    try:
        net = IPy.IP(f"{first_ip}/{totalbits - hostbits}")
    except ValueError:
        return fallback
    if net[0] == first_ip and net[-1] == last_ip:
        return str(net)
    else:
        return fallback

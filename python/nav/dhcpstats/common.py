#
# Copyright (C) 2026 Sikt
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
#
"""
Common classes and functions used by DHCP API clients and various other parts of
NAV that wants to make use of DHCP stats.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Literal, Optional, Union

import IPy

from nav.metrics.graphs import (
    aliased_series,
    json_graph_url,
    nonempty_series,
    summed_series,
)
from nav.metrics.names import get_expanded_nodes, safe_name
from nav.metrics.templates import metric_path_for_dhcp


_logger = logging.getLogger(__name__)

# Type expected by functions in NAV that send stats to a Graphite/Carbon backend. Values
# of this type are interpreted as (path, (timestamp, value)).
GraphiteMetric = tuple[str, tuple[float, int]]


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


def group_paths(paths: list["DhcpPath"]):
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
    grouped_paths: list[list["DhcpPath"]], prefixes: list[IPy.IP]
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


@dataclass(frozen=True, order=True)
class DhcpPath:
    """
    Represents a path to a DHCP stat in Graphite sans the stat's metric_name.
    The absence of metric_name means that all of the following DHCP stat paths
    in Graphite:

      nav.dhcp.servers.kea-osl.range.custom_groups.staff.4.1_0_1_1.1_0_1_255.assigned
      nav.dhcp.servers.kea-osl.range.custom_groups.staff.4.1_0_1_1.1_0_1_255.total
      nav.dhcp.servers.kea-osl.range.custom_groups.staff.4.1_0_1_1.1_0_1_255.declined

    are represented by:

      DhcpPath(
          ip_version=4,
          server_name"kea-osl",
          allocation_type="range",
          group_name_source="custom_groups",
          group_name="staff",
          first_ip=IP("1.0.1.1"),
          last_ip=IP("1.0.1.255"),
      )

    Instantiate me via :meth from_external_info: if path data is sourced from an
     external source such as a DHCP server.
    Instantiate me via :meth from_graphite_path: if path data is sourced from
     NAV's Graphite database.
    Use me to do the following translations, with validity checks:
     external info (from DHCP server) --> DhcpPath <--> Graphite path
    """

    # Fields are ordered according to how we want instances to be sorted,
    # *not* how fields occur in the respective paths in Graphite
    server_name: str
    group_name_source: Literal["special_groups", "custom_groups"]
    group_name: str
    allocation_type: Literal["range", "pool", "subnet"]
    ip_version: int
    first_ip: IPy.IP
    last_ip: IPy.IP

    @classmethod
    def from_graphite_path(cls, graphite_path: str):
        """
        Instantiate me from a path to a DHCP stat (either sans metric_name or
        not) from Graphite.

        >>> d = {"server_name": "foo", "allocation_type": "pool",
        ...   "group_name": None, "first_ip": "::1", "last_ip": "::2"}
        >>> my_path = DhcpPath.from_external_info(**d)
        >>> graphite_path = my_path.to_graphite_path("bar")
        >>> graphite_path
        'nav.dhcp.servers.foo.pool.special_groups.standalone.6.0_0_0_0_0_0_0_1.0_0_0_0_0_0_0_2.bar'
        >>> DhcpPath.from_graphite_path(graphite_path) == my_path
        True
        """
        parts = graphite_path.split(".")
        if not len(parts) >= 10:
            raise ValueError(
                f"Expected graphite_path {graphite_path!r} to have at least 10 "
                f"dot-separated segments"
            )
        server_name = parts[3]
        allocation_type = parts[4]
        group_name_source = parts[5]
        group_name = parts[6]
        ip_version = parts[7]
        first_ip = parts[8]
        last_ip = parts[9]

        allowed_group_sources = ("special_groups", "custom_groups")
        if group_name_source not in allowed_group_sources:
            raise ValueError(
                f"group_source_name {group_name_source!r} is not in "
                f"{allowed_group_sources!r}"
            )

        allowed_allocation_types = ("range", "pool", "subnet")
        if allocation_type not in allowed_allocation_types:
            raise ValueError(
                f"allocation_type {allocation_type!r} is not in "
                f"{allowed_allocation_types!r}"
            )

        first_ip = cls._unescape_graphite_address(first_ip)
        last_ip = cls._unescape_graphite_address(last_ip)
        cls._check_ip_pair(first_ip, last_ip)

        if (
            str(first_ip.version()) != ip_version
            or str(last_ip.version()) != ip_version
        ):
            raise ValueError(
                f"first_ip {first_ip!r} or last_ip {last_ip!r} not of same version as "
                f"expected ip_version {ip_version!r}"
            )

        return cls(
            ip_version=first_ip.version(),
            server_name=server_name,
            allocation_type=allocation_type,
            group_name_source=group_name_source,
            group_name=group_name,
            first_ip=first_ip,
            last_ip=last_ip,
        )

    @classmethod
    def from_external_info(
        cls,
        server_name: str,
        allocation_type: Literal["range", "pool", "subnet"],
        group_name: Optional[str],
        first_ip: Union[str, IPy.IP],
        last_ip: Union[str, IPy.IP],
    ):
        """
        Instantiate me with path data sourced from an external source such as a
        DHCP server.

        if group_name is missing, group_name_source is set to "special_groups"
         and group_name is set to "standalone" such that the returned instance
         will be treated as belonging to a group of size one.
        otherwise, group_name_source is set to "custom_groups".

        if first_ip cannot be parsed to an IP address, raises a ValueError
        if last_ip cannot be parsed to an IP address, raises a ValueError
        if first_ip and last_ip does not have the same IP version, raises a ValueError
        if first_ip > last_ip, raises a ValueError
        otherwise, returns a DhcpPath instance.
        """
        if group_name is None:
            group_name_source = "special_groups"
            group_name = "standalone"
        else:
            group_name_source = "custom_groups"

        first_ip = IPy.IP(first_ip)
        last_ip = IPy.IP(last_ip)
        cls._check_ip_pair(first_ip, last_ip)

        return cls(
            ip_version=first_ip.version(),
            server_name=server_name,
            allocation_type=allocation_type,
            group_name_source=group_name_source,
            group_name=group_name,
            first_ip=first_ip,
            last_ip=last_ip,
        )

    def to_graphite_path(self, metric_name, wildcard_for_group=False):
        """
        Return me as a path recognized by Graphite.
        """
        if wildcard_for_group and not self.is_standalone():
            first_ip = safe_name("*")
            last_ip = safe_name("*")
        else:
            first_ip = self.first_ip.strNormal()
            last_ip = self.last_ip.strNormal()

        return metric_path_for_dhcp(
            ip_version=self.ip_version,
            server_name=self.server_name,
            allocation_type=self.allocation_type,
            group_name_source=self.group_name_source,
            group_name=self.group_name,
            first_ip=first_ip,
            last_ip=last_ip,
            metric_name=metric_name,
        )

    def intersects(self, prefixes: Iterable[IPy.IP]):
        """
        Check if the range of IP addresses between self.first_ip and self.last_ip
        intersect with any of the given prefixes.
        """
        return any(
            self.first_ip in prefix
            or self.last_ip in prefix
            or self.first_ip < prefix < self.last_ip
            for prefix in prefixes
        )

    @staticmethod
    def _unescape_graphite_address(escaped_address: str) -> IPy.IP:
        parts = escaped_address.split("_")
        if len(parts) == 4:
            return IPy.IP(".".join(parts))
        elif len(parts) == 8:
            return IPy.IP(":".join(parts))
        else:
            raise ValueError(
                f"{escaped_address!r} does not look like an escaped IP address"
            )

    @staticmethod
    def _check_ip_pair(first_ip: IPy.IP, last_ip: IPy.IP):
        if len(first_ip) != 1:
            raise ValueError(f"first_ip {first_ip!r} must be an IP address")

        if len(last_ip) != 1:
            raise ValueError(f"last_ip {last_ip!r} must be an IP address")

        if first_ip.version() != last_ip.version():
            raise ValueError(
                f"first_ip {first_ip!r} is not of same version as last_ip {last_ip!r}"
            )

        if first_ip > last_ip:
            raise ValueError(f"first_ip {first_ip!r} greater than last_ip {last_ip!r}")

    def is_standalone(self):
        return (
            self.group_name_source == "special_groups"
            and self.group_name == "standalone"
        )

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

from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Union

import IPy

from nav.metrics.names import safe_name
from nav.metrics.templates import metric_path_for_dhcp


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

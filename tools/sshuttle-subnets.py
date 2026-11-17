#!/usr/bin/env python3
#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Reduces the management IP addresses of NAV's netboxes to a list of subnets
suitable for routing through an sshuttle tunnel.

Addresses are grouped into fixed-size buckets (by default /24 for IPv4 and
/64 for IPv6). A bucket holding at least --min-hosts of the addresses is
routed as a whole; addresses in sparser buckets get a host route each.
Adjacent results are then merged, which never adds addresses that were not
already covered. With --host-routes, every address is output as-is instead.

Example:
  sshuttle --method tproxy -r jumphost \\
    $(tools/sshuttle-subnets.py "filter(type__vendor__id='juniper')")
"""

import argparse
import ipaddress
import sys
from collections import defaultdict

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.models.manage import Netbox  # noqa: E402


def main():
    args = parse_args()
    addresses = get_netbox_addresses(args.filter)
    if not addresses:
        # stderr stays visible even when output is captured by $(...)
        sys.exit("No netboxes matched")
    if args.host_routes:
        subnets = to_host_routes(addresses)
    else:
        subnets = reduce_to_subnets(
            addresses,
            bucket_sizes={4: args.v4_bucket, 6: args.v6_bucket},
            min_hosts=args.min_hosts,
        )
    for subnet in subnets:
        print(subnet)
    if args.verbose:
        report(addresses, subnets)


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "filter",
        nargs="?",
        help="A method call on the Netbox model's manager, just like navdf "
        "accepts. Example: \"filter(category__id='GSW')\"",
    )
    parser.add_argument(
        "-4",
        "--v4-bucket",
        type=int_range(0, 32),
        default=24,
        metavar="LEN",
        help="IPv4 bucket prefix length (default: %(default)s). Adjacent "
        "routed buckets may still merge into a larger subnet",
    )
    parser.add_argument(
        "-6",
        "--v6-bucket",
        type=int_range(0, 128),
        default=64,
        metavar="LEN",
        help="IPv6 bucket prefix length (default: %(default)s). Adjacent "
        "routed buckets may still merge into a larger subnet",
    )
    parser.add_argument(
        "-m",
        "--min-hosts",
        type=int_range(1),
        default=2,
        metavar="N",
        help="route a whole bucket only if it holds at least N addresses; "
        "otherwise use host routes (default: %(default)s)",
    )
    parser.add_argument(
        "-H",
        "--host-routes",
        action="store_true",
        help="output one /32 or /128 per address, without bucketing or "
        "merging (overrides -4, -6 and -m)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="report how many addresses each subnet covers, on stderr",
    )
    return parser.parse_args()


def get_netbox_addresses(filter_expression=None):
    """Returns the set of netbox management IP addresses matching a filter"""
    if filter_expression:
        # Same trust model as navdf: this is a developer tool, and the
        # expression comes from the person running it.
        queryset = eval("Netbox.objects." + filter_expression)
    else:
        queryset = Netbox.objects.all()
    return {ipaddress.ip_address(ip) for ip in queryset.values_list("ip", flat=True)}


def to_host_routes(addresses):
    """Returns a sorted list of one host route per address"""
    return sorted(
        (ipaddress.ip_network(addr) for addr in addresses),
        key=lambda net: (net.version, net),
    )


def reduce_to_subnets(addresses, bucket_sizes, min_hosts):
    """Reduces a set of IP addresses to a sorted list of subnets.

    :param bucket_sizes: dict mapping IP version (4, 6) to bucket prefix length.
    :param min_hosts: smallest number of addresses for which a whole bucket
                      will be routed.
    """
    buckets = defaultdict(list)
    for address in addresses:
        bucket = ipaddress.ip_network(address).supernet(
            new_prefix=bucket_sizes[address.version]
        )
        buckets[bucket].append(address)

    subnets = []
    for bucket, members in buckets.items():
        if len(members) >= min_hosts:
            subnets.append(bucket)
        else:
            subnets.extend(ipaddress.ip_network(addr) for addr in members)
    return collapse_per_version(subnets)


def collapse_per_version(subnets):
    """Merges adjacent and overlapping subnets, keeping families apart"""
    result = []
    for version in (4, 6):
        same_family = [net for net in subnets if net.version == version]
        result.extend(ipaddress.collapse_addresses(same_family))
    return result


def report(addresses, subnets):
    """Prints how many of the addresses each subnet covers, on stderr"""
    for subnet in subnets:
        count = sum(addr in subnet for addr in addresses)
        print(f"# {subnet}: {count} address(es)", file=sys.stderr)
    print(
        f"# {len(addresses)} addresses reduced to {len(subnets)} subnets",
        file=sys.stderr,
    )


def int_range(minimum, maximum=None):
    """Returns an argparse type function that accepts integers in a range.

    A maximum of None means there is no upper bound.
    """
    if maximum is None:
        expected = f"an integer >= {minimum}"
    else:
        expected = f"an integer between {minimum} and {maximum}"

    def integer(value):
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{value!r} is not {expected}")
        if number < minimum or (maximum is not None and number > maximum):
            raise argparse.ArgumentTypeError(f"{value!r} is not {expected}")
        return number

    return integer


if __name__ == "__main__":
    main()

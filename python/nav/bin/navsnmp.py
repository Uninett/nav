#!/usr/bin/env python
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
#
"""Outputs NAV's SNMP configuration for input devices as NET-SNMP compatible command
line arguments.

"""

import argparse
import sys

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.models.manage import Netbox
from IPy import IP


def main():
    """Main program"""
    args = parse_args()
    if args.sysname:
        boxes = get_matching_boxes([args.sysname])
    else:
        boxes = get_matching_boxes(sys.stdin.readlines())

    for netbox in boxes:
        snmp_printer(netbox)


def parse_args():
    """Builds an ArgumentParser and returns parsed program arguments"""
    parser = argparse.ArgumentParser(
        description=__doc__.replace("\n", " ").strip(),
        epilog="Example usage:\nsnmpwalk $(%(prog)s example-sw.example.org) "
        "SNMPv2-MIB::system ",
    )
    parser.add_argument(
        "sysname",
        nargs='?',
        help="sysname of device whose configuration should be "
        "output. If omitted, a list of names is taken "
        "from stdin instead.",
    )
    return parser.parse_args()


def get_matching_boxes(patterns):
    result = []
    for pattern in patterns:
        sysname = pattern.strip()
        boxes = Netbox.objects.filter(sysname__startswith=sysname)
        if boxes:
            result.extend(boxes)
        else:
            print("no match for %s" % pattern, file=sys.stderr)
    return result


def snmp_printer(netbox):
    profile = netbox.get_preferred_snmp_management_profile()
    try:
        version = profile.snmp_version
        if version == 2:
            version = "2c"
    except (AttributeError, ValueError):
        version = None

    if not profile or not version:
        print("%s has no valid SNMP configuration in NAV" % netbox, file=sys.stderr)
        return

    ipaddr = IP(netbox.ip)
    if ipaddr.version() == 6:
        ipaddr = "ipv6:[%s]" % ipaddr

    print("# {}".format(netbox.sysname), file=sys.stderr)

    args = [f"-v{version}"]
    if version != 3:
        args.append(f"-c {profile.snmp_community}")
    else:
        conf = profile.configuration
        args.extend(["-l", conf["sec_level"], "-u", conf["sec_name"]])
        if conf.get("auth_protocol"):
            args.extend(["-a", conf.get("auth_protocol")])
        if conf.get("auth_password"):
            args.extend(["-A", conf.get("auth_password")])
        if conf.get("priv_protocol"):
            args.extend(["-x", conf.get("priv_protocol")])
        if conf.get("priv_password"):
            args.extend(["-X", conf.get("priv_password")])

    args.append(ipaddr)

    print(" ".join(str(i) for i in args))


if __name__ == '__main__':
    main()

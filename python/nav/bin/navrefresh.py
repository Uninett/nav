#!/usr/bin/env python3
# -*- testargs: -h -*-
#
# Copyright 2025 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""A command line interface to send refresh commands to a running ipdevpoll daemon"""

import argparse
import sys

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from django.db import transaction
from nav.models.manage import Netbox
from nav.event2 import EventFactory

RefreshEvent = EventFactory("devBrowse", "ipdevpoll", event_type="notification")


def main():
    """Main program"""
    args = parse_args()
    if not args.netbox:
        sys.exit(f"Sysname pattern {args.netbox.pattern!r} matched nothing")

    send_refresh_events(args.netbox, args.job)


@transaction.atomic
def send_refresh_events(netboxes: list[Netbox], job: str):
    """Sends refresh events for all selected netboxes for the selected job"""
    for netbox in netboxes:
        print(f"Sending refresh event for {netbox.sysname} job {job}")
        event = RefreshEvent.notify(netbox=netbox, subid=job)
        event.save()


def parse_args():
    """Builds an ArgumentParser and returns parsed program arguments"""
    parser = argparse.ArgumentParser(
        description="Sends job refresh commands to a running ipdevpoll daemon",
    )
    parser.add_argument(
        "netbox",
        type=SysnamePattern,
        help="sysname (or sysname prefix) of devices that should be refreshed. Be "
        "aware that multiple devices can match.",
    )
    parser.add_argument("job", type=non_empty_string, help="ipdevpoll job to refresh.")
    return parser.parse_args()


class SysnamePattern(list):
    """Looks up netboxes based on sysname patterns from arguments"""

    def __init__(self, pattern: str):
        super().__init__()
        self.pattern = pattern.strip() if pattern else ""
        if not self.pattern:
            raise ValueError("sysname pattern cannot be empty")
        self.extend(Netbox.objects.filter(sysname__startswith=self.pattern))


def non_empty_string(value: str):
    """Validates a string to be non-empty"""
    if not value.strip():
        raise argparse.ArgumentTypeError("cannot be empty")
    return value.strip()


if __name__ == '__main__':
    main()

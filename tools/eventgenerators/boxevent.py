#!/usr/bin/env python
#
# Copyright (C) 2015, 2019 Uninett AS
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
"""Script to simulate up/down events from pping"""

from __future__ import print_function
import argparse
import sys

from nav.bootstrap import bootstrap_django
bootstrap_django()

from nav.models.event import EventQueue as Event, Subsystem, EventType
from nav.models.manage import Netbox
from django.db import transaction


DEFAULT_KWARGS = {
    'source': Subsystem.objects.get(pk='pping'),
    'target': Subsystem.objects.get(pk='eventEngine'),
    'event_type': EventType.objects.get(pk='boxState')
}


@transaction.atomic
def main():
    """Main script controller"""
    args = create_parser().parse_args()

    for sysname in args.sysname:
        boxes = Netbox.objects.filter(sysname__icontains=sysname)
        if boxes.exists():
            for netbox in boxes:
                send_event(netbox, args.event, send=args.dry_run)
        else:
            print("No netboxes matched: %r" % args.sysname, file=sys.stderr)
            exit(1)


def create_parser():
    """Create a parser for the script arguments"""
    parser = argparse.ArgumentParser(
        description='Script to simulate up/down events from pping')
    parser.add_argument('event', help='Type of event to simulate',
                        choices=['up', 'down'])
    parser.add_argument('sysname', nargs='+',
                        help='Sysname used to filter netboxes')
    parser.add_argument('--dry-run', action='store_false',
                        help='Print the events to be sent without sending them')
    return parser


def send_event(netbox, event_spec, send=True):
    """Send a boxstate event for a given netbox"""
    event = Event(**DEFAULT_KWARGS)
    event.netbox = netbox
    event.state = Event.STATE_END if event_spec == 'up' else Event.STATE_START
    print(event)

    if send:
        event.save()


if __name__ == '__main__':
    main()

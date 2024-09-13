#!/usr/bin/env python3
#
# Copyright (C) 2007, 2012, 2015 Uninett AS
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
"""Script to simulate link up/down events from snmptrapd / ipdevpoll"""

import argparse

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.models.event import EventQueue as Event, Subsystem, EventType
from nav.models.manage import Interface
from django.db import transaction


DEFAULT_KWARGS = {
    'source': Subsystem.objects.get(pk='ipdevpoll'),
    'target': Subsystem.objects.get(pk='eventEngine'),
    'event_type': EventType.objects.get(pk='linkState'),
}


@transaction.atomic
def main():
    """Main script controller"""
    args = create_parser().parse_args()

    for sysname, ifname in args.interfaces:
        for interface in Interface.objects.filter(
            netbox__sysname__icontains=sysname, ifname=ifname
        ):
            send_event(interface, args.event, send=args.dry_run)


def interface_spec(spec):
    sysname, ifname = spec.split(":", 1)
    return sysname, ifname


def create_parser():
    """Create a parser for the script arguments"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'event', help='Type of event to simulate', choices=['up', 'down']
    )
    parser.add_argument(
        'interfaces',
        metavar='sysname:ifname',
        nargs='+',
        type=interface_spec,
        help='Select which interfaces to make events for',
    )
    parser.add_argument(
        '--dry-run',
        action='store_false',
        help='Print the events to be sent without sending them',
    )
    return parser


def send_event(interface, event_spec, send=True):
    """Send a linkState event for a given interface"""
    event = Event(**DEFAULT_KWARGS)
    event.netbox = interface.netbox
    event.subid = interface.pk
    event.state = Event.STATE_END if event_spec == 'up' else Event.STATE_START
    print(
        "{type} {state} event for {subject}".format(
            type=event.event_type_id,
            state="start" if event.state == Event.STATE_START else "end",
            subject=event.get_subject(),
        )
    )

    if send:
        event.save()


if __name__ == '__main__':
    main()

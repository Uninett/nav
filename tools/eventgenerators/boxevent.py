#!/usr/bin/python
#
# $Id$
#
# Copyright 2015 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""Script to simulate up/down events from pping"""

from __future__ import print_function
import argparse

from nav.models.event import EventQueue as Event, Subsystem, EventType
from nav.models.manage import Netbox

DEFAULT_KWARGS = {
    'source': Subsystem.objects.get(pk='pping'),
    'target': Subsystem.objects.get(pk='eventEngine'),
    'event_type': EventType.objects.get(pk='boxState')
}

def main():
    """Main script controller"""
    args = create_parser().parse_args()

    for netbox in Netbox.objects.filter(sysname__icontains=args.sysname):
        send_event(netbox, args.event, send=args.dry_run)


def create_parser():
    """Create a parser for the script arguments"""
    parser = argparse.ArgumentParser(
        description='Script to simulate up/down events from pping')
    parser.add_argument('sysname', help='Sysname used to filter netboxes')
    parser.add_argument('event', help='Type of event to simulate',
                        choices=['up', 'down'])
    parser.add_argument('--dry-run', action='store_false',
                        help='Print the events to be sent without sending them')
    return parser


def send_event(netbox, event_spec, send=True):
    """Send a boxstate event for a given netbox"""
    event = Event(**DEFAULT_KWARGS)
    event.netbox = netbox
    event.state = 'e' if event_spec == 'up' else 's'
    print(event)

    if send:
        event.save()


if __name__ == '__main__':
    main()

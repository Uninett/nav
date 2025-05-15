#!/usr/bin/env python3
#
# Copyright (C) 2012 Uninett AS
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
"""Module comment"""

from argparse import ArgumentParser

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.event import Event
from nav.models.event import EventQueue, EventType
from nav.models.manage import Netbox


def main():
    """Main controller"""
    namespace = parse_options()

    netbox = Netbox.objects.get(sysname__icontains=namespace.sysname)
    eventtype = EventType.objects.get(pk__icontains=namespace.eventtype)
    event = Event(
        source="ipdevpoll",
        target="eventEngine",
        netboxid=netbox.id,
        subid=namespace.subid,
        eventtypeid=eventtype.id,
        state=get_state(namespace),
    )

    if namespace.alerttype:
        event['alerttype'] = namespace.alerttype
    event.post()


def parse_options():
    """Parse command line options and args"""
    parser = ArgumentParser()
    parser.add_argument(
        '-e', dest='eventtype', required=True, help='The name of the event type'
    )
    parser.add_argument('-n', dest='sysname', required=True, help='Netbox sysname')
    parser.add_argument('-a', dest='alerttype', help='The name of the alert type')
    parser.add_argument('--subid', dest='subid', default=None, help='The subid to use')
    parser.add_argument(
        'state',
        choices=('s', 'e'),
        help='The state of the event (nothing if stateless)',
    )
    return parser.parse_args()


def get_state(args):
    """Return correct event state based on args"""
    if not args:
        return EventQueue.STATE_STATELESS
    else:
        return (
            EventQueue.STATE_START
            if args.state.startswith('s')
            else EventQueue.STATE_END
        )


if __name__ == '__main__':
    main()

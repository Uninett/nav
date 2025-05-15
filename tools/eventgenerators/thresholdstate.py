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
"""Module to fake thresholdstate events

This will create fake events and insert them into the database. Use for
testing purposes only.

"""

import sys

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.models.event import EventQueue as Event, Subsystem, EventType
from nav.models.manage import Netbox


def main():
    """Main controller"""
    if len(sys.argv) <= 2:
        print("Need netbox and eventstate")
        sys.exit()

    netboxarg = sys.argv[1]
    eventstate = sys.argv[2]
    try:
        subid = sys.argv[3]
    except IndexError:
        subid = ""

    try:
        netbox = Netbox.objects.get(sysname__icontains=netboxarg)
    except Netbox.DoesNotExist:
        print("No netbox found")
        sys.exit()

    if eventstate[0] not in ['u', 'd']:
        print("Specify [u]p or [d]own event")
        sys.exit()

    source = Subsystem.objects.get(pk='thresholdMon')
    target = Subsystem.objects.get(pk='eventEngine')
    eventtype = EventType.objects.get(pk='thresholdState')

    state = 's' if eventstate.startswith('d') else 'e'

    #    oid = 'cpu1min'
    #    value = '90'
    event = Event(
        source=source,
        target=target,
        subid=subid,
        netbox=netbox,
        event_type=eventtype,
        state=state,
    )
    event.save()


if __name__ == '__main__':
    main()

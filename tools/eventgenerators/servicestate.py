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
"""Module to fake servicestate events

This will create fake events and insert them into the database. Use for
testing purposes only.

"""

import sys
from optparse import OptionParser

from nav.bootstrap import bootstrap_django

bootstrap_django()

from nav.models.event import EventQueue as Event, Subsystem, EventType
from nav.models.manage import Netbox
from nav.models.service import Service


def main():
    """Main controller"""

    parser = create_parser()
    (options, _) = parser.parse_args()
    verify_options(options, parser)

    if options.list_services:
        print_services()
        sys.exit()

    try:
        netbox = Netbox.objects.get(sysname__icontains=options.netbox)
    except Netbox.DoesNotExist:
        parser.error("No netbox found")
        sys.exit()

    source = Subsystem.objects.get(pk='serviceping')
    target = Subsystem.objects.get(pk='eventEngine')
    eventtype = EventType.objects.get(pk='serviceState')

    state = 's' if options.state.startswith('d') else 'e'

    event = Event(
        source=source,
        target=target,
        subid=options.subid,
        netbox=netbox,
        event_type=eventtype,
        device=netbox.device,
        state=state,
    )
    event.save()


def create_parser():
    """Create optionparser"""
    parser = OptionParser(usage="Event needs netbox, state and subid")
    parser.add_option("-n", dest="netbox", help="part of sysname for netbox")
    parser.add_option("-i", dest="subid", help="id of service to send event for")
    parser.add_option("-s", dest="state", help="specify [u]p or [d]own event")
    parser.add_option(
        "-l", action="store_true", dest="list_services", help="List current services"
    )
    return parser


def verify_options(options, parser):
    """Verify the input from the user"""

    if options.list_services:
        return

    if not (options.netbox and options.subid and options.state):
        parser.error("Need all options to post event")

    if options.state[0].lower() not in ['u', 'd']:
        parser.error("Specify [u]p or [d]own event")


def print_services():
    """Print services used for subid"""
    services = Service.objects.all()
    string_format = "%3s - %s"
    print(string_format % ("ID", "Service"))
    for service in services:
        print(string_format % (service.id, service))


if __name__ == '__main__':
    main()

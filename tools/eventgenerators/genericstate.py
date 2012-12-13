#!/usr/bin/env python
#
# Copyright (C) 2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module comment"""

from optparse import OptionParser
from nav.models.event import EventQueue as Event, Subsystem, EventType
from nav.models.manage import Netbox


def main():
    """Main controller"""
    (options, args) = parse_options()

    source = Subsystem.objects.get(name='ipdevpoll')
    target = Subsystem.objects.get(name='eventEngine')
    netbox = Netbox.objects.get(sysname__icontains=options.sysname)
    device = netbox.device
    eventtype = EventType.objects.get(pk__icontains=options.eventtype)

    event = Event(source=source, target=target, netbox=netbox, device=device,
                  event_type=eventtype, state=get_state(args))
    event.varmap = {'alerttype': options.alerttype}
    event.save()


def parse_options():
    """Parse command line options and args"""
    parser = OptionParser(usage="%prog [options] state")
    parser.add_option('-e', dest='eventtype')
    parser.add_option('-a', dest='alerttype')
    parser.add_option('-n', dest='sysname', help='Netbox sysname')
    return parser.parse_args()


def get_state(args):
    """Return correct event state based on args"""
    if not args:
        return Event.STATE_STATELESS
    else:
        return (Event.STATE_START if args[0].startswith('d')
                else Event.STATE_END)

if __name__ == '__main__':
    main()

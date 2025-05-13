#!/usr/bin/env python3
#
# Copyright (C) 2023 Sikt
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

from nav.event2 import EventFactory
from nav.models.manage import Device


def main():
    """Main controller"""
    args = parse_options()

    device = Device.objects.get(serial=args.serial)
    event = EventFactory('ipdevpoll', 'eventEngine', 'deviceNotice')
    event.notify(
        device=device,
        alert_type=args.alerttype,
        varmap={
            "old_version": "old",
            "new_version": "new",
        },
    ).save()


def parse_options():
    """Parse command line options and args"""
    parser = ArgumentParser()
    parser.add_argument('-s', dest='serial', required=True, help='Serial of device')
    parser.add_argument(
        '-a', dest='alerttype', required=True, help='The name of the alert type'
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()

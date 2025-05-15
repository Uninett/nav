#!/usr/bin/env python
#
# Copyright (C) 2014, 2016 Uninett AS
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
"""
A command line interface to list and filter IP devices monitored by NAV
"""

import argparse

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.models.manage import Netbox


def main():
    """Main program"""
    args = parse_args()
    if args.filter:
        qs = eval('Netbox.objects.' + args.filter)
    else:
        qs = Netbox.objects.all()

    for netbox in qs.order_by('sysname').values_list('sysname', flat=1):
        print(netbox)


def parse_args():
    """Builds an ArgumentParser and returns parsed program arguments"""
    parser = argparse.ArgumentParser(
        description="Lists and filters IP devices monitored by NAV",
        usage="%(prog)s [filter]",
    )
    parser.add_argument(
        'filter',
        nargs='?',
        help="The filter expression must be a method call "
        "applicable to the Django-based Netbox model's "
        "manager class. Example: "
        "\"filter(category__id='GSW')\"",
    )
    return parser.parse_args()


if __name__ == '__main__':
    main()

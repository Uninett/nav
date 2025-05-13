#!/usr/bin/env python
# -*- testargs: 127.0.0.1 localhost dummy -*-
#
# Copyright (C) 2015 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

"""
Utility to run one NAV servicemon checker plugin against an arbitrary
host. Useful for testing or debugging individual servicemon plugins.

"""

import argparse
import sys

import IPy
import logging

from nav.logs import init_stderr_logging
from nav.statemon import checkermap


_logger = logging.getLogger('nav.checkservice')


def main():
    init_stderr_logging()
    cargs = parse_args()
    _logger.debug(
        "Ip: %s sysname: %s handler: %r", cargs.ip, cargs.sysname, cargs.handler
    )
    checker = checkermap.get(cargs.handler)
    if not checker:
        _logger.fatal("Could not create checker instance")
        sys.exit(1)
    args = read_checker_args(checker)
    _logger.debug("Input args: %r", args)

    service = {
        'id': 0,
        'netboxid': 0,
        'deviceid': 0,
        'ip': str(cargs.ip),
        'sysname': cargs.sysname,
        'args': args,
        'version': "",
    }

    print("Checking")
    my_checker = checker(service)
    print('  Return value:', my_checker.execute())
    print('       Version:', repr(my_checker.version))
    print("Finished")


def parse_args():
    checkermap.parsedir()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        'ip', metavar='IP', type=IPy.IP, help='IP address of host to check'
    )
    parser.add_argument(
        'sysname',
        metavar='SYSNAME',
        help='Name to associate with this device. Does not '
        'need to a be real name in any sense.',
    )
    parser.add_argument(
        'handler',
        metavar='HANDLER',
        choices=checkermap.checkers.keys(),
        help='Handler name of the checker plugin to use. Available handler plugins are '
        + ', '.join(checkermap.checkers.keys())
        + '.',
    )
    return parser.parse_args()


def read_checker_args(checker):
    args = {}
    if checker.ARGS:
        print(
            "{} requires these arguments: {}".format(
                checker.__name__, ", ".join(arg[0] for arg in checker.ARGS)
            )
        )
    if checker.OPTARGS:
        print(
            "{} takes these optional arguments: {}".format(
                checker.__name__, ", ".join(arg[0] for arg in checker.OPTARGS)
            )
        )
    if not (checker.ARGS or checker.OPTARGS):
        print("{} takes no extra arguments".format(checker.__name__))
        return args

    print("Input checker arguments (key=val), empty line to continue:")
    while True:
        try:
            line = input()
        except EOFError:
            line = ""
        if not line:
            break
        try:
            key, val = line.split('=', 1)
            args[key] = val
        except ValueError:
            print("Must be on form 'key=val'")
    return args


if __name__ == '__main__':
    main()

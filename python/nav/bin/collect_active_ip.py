#!/usr/bin/env python
# -*- testargs: -h -*-
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
"""A wrapper for prefix_ip_collector"""

import argparse
import logging
import time
import sys

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

import nav.daemon
from nav.activeipcollector import manager
from nav.logs import init_generic_logging

PIDFILE = 'collect_active_ip.pid'
LOGFILE = 'collect_active_ip.log'
_logger = logging.getLogger('nav.ipcollector')


def main(args=None):
    """Controller"""
    if args is None:
        args = get_parser().parse_args()
    days = args.days or None
    exit_if_already_running()
    init_generic_logging(logfile=LOGFILE, stderr=False)
    run(days)


def exit_if_already_running():
    """Exits the process if another process is running or write pid if not"""
    try:
        nav.daemon.justme(PIDFILE)
        nav.daemon.writepidfile(PIDFILE)
    except nav.daemon.DaemonError as error:
        print(error)
        sys.exit(1)


def run(days):
    """Run this collection"""
    _logger.info('Starting active ip collector')
    starttime = time.time()
    manager.run(days)
    _logger.info('Done in %.2f seconds', time.time() - starttime)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--days",
        default=None,
        type=int,
        help="days back in time to start collecting from",
    )

    return parser


if __name__ == '__main__':
    main()

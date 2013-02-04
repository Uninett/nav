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
"""A wrapper for prefix_ip_collector"""

import ConfigParser
from optparse import OptionParser
import logging
import time
import sys
from os.path import join

import nav.daemon
from nav import logs
from nav.activeipcollector import manager
from nav.path import localstatedir, sysconfdir

PIDFILE = join(localstatedir, 'run', 'collect_active_ip.pid')
LOGFILE = join(localstatedir, 'log', 'collect_active_ip.log')
_logger = logging.getLogger('ipcollector')


def main(days=None, reset=False):
    """Controller"""
    init_logger(LOGFILE)
    exit_if_already_running()
    run(days, reset)


def exit_if_already_running():
    """Exits the process if another process is running or write pid if not"""
    try:
        nav.daemon.justme(PIDFILE)
        nav.daemon.writepidfile(PIDFILE)
    except nav.daemon.DaemonError, error:
        print error
        sys.exit(1)


def run(days, reset):
    """Run this collection"""
    _logger.info('Starting active ip collector')
    starttime = time.time()

    datadir = join(get_datadir(), 'activeip')
    errors = manager.run(datadir, days, reset)
    if errors:
        print '%s errors - see log' % errors
    _logger.info('Done in %.2f seconds' % (time.time() - starttime))


def init_logger(logfile):
    """Create logger for this process"""
    logs.set_log_levels()

    filehandler = logging.FileHandler(logfile)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] '
                                  '[%(name)s] %(message)s')
    filehandler.setFormatter(formatter)
    root = logging.getLogger('')
    root.addHandler(filehandler)


def get_datadir():
    """Get datadir"""
    return join(localstatedir, 'rrd')


def get_cricket_conf():
    """Find entry in mcc.conf that specifies location of cricket_conf.pl"""
    config = ConfigParser.ConfigParser()
    config.read(join(sysconfdir, 'mcc.conf'))
    return config.get('mcc', 'configfile')


if __name__ == '__main__':
    PARSER = OptionParser()
    PARSER.add_option("-d", "--days", dest="days", default=None, type="int",
                      help="Days back in time to start collecting from")
    PARSER.add_option("-r", "--reset", dest="reset", default=False,
                      action="store_true",
                      help="Delete existing rrd-files. Use it with --days to "
                           "refill")

    OPTIONS, _ = PARSER.parse_args()

    main(OPTIONS.days, OPTIONS.reset)

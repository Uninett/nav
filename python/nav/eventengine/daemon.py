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
"eventengine daemon interface"

import sys
import os
import logging
from optparse import OptionParser

from nav import buildconf
import nav.daemon
import nav.logs
from nav.eventengine import EventEngine


PIDFILE = os.path.join(
    buildconf.localstatedir, 'run', 'eventengine.pid')
LOGFILE = os.path.join(
    buildconf.localstatedir, 'log', 'eventengine.log')
_logger = logging.getLogger(__name__)

def main():
    "main execution entry"
    options, _args = parse_options()
    initialize_logging(options)
    exit_if_already_running()
    if not options.foreground:
        daemonize()
    start_engine()

def parse_options():
    "Parses the program's command line options"
    parser = make_option_parser()
    options, args = parser.parse_args()
    return options, args

def make_option_parser():
    "Makes an OptionParser instance for the program"
    parser = OptionParser(
        version="NAV " + buildconf.VERSION,
        epilog=("This program monitors NAV's event queue and decides which "
                "actions to take when events occur")
        )
    opt = parser.add_option
    opt("-f", "--foreground", action="store_true", dest="foreground",
        help="run in foreground instead of daemonizing")

    return parser

def initialize_logging(options=None):
    "Initializes logging"
    fmt = logging.Formatter("%(asctime)s [%(levelname)s %(name)s] %(message)s")
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(fmt)

    root_logger = logging.getLogger('')
    root_logger.addHandler(stderr_handler)

    nav.logs.set_log_levels()

    if not options.foreground:
        file_handler = logging.FileHandler(LOGFILE, 'a')
        file_handler.setFormatter(fmt)

        root_logger.addHandler(file_handler)
        root_logger.removeHandler(stderr_handler)
        nav.daemon.redirect_std_fds(
            stderr=nav.logs.get_logfile_from_logger())

def exit_if_already_running():
    "Exits the process if another eventengine process is already running"
    try:
        nav.daemon.justme(PIDFILE)
    except nav.daemon.DaemonError, error:
        _logger.error(error)
        sys.exit(1)

def daemonize():
    "Daemonizes the program"
    try:
        nav.daemon.daemonize(PIDFILE,
                             stderr=nav.logs.get_logfile_from_logger())
    except nav.daemon.DaemonError, error:
        _logger.fatal(error)
        sys.exit(1)

def start_engine():
    "Starts event queue processing"
    engine = EventEngine()
    engine.start()

if __name__ == '__main__':
    main()

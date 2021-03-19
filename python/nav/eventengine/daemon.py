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
"eventengine daemon interface"

import sys
import os
import logging
from optparse import OptionParser
import signal

from nav import buildconf
import nav.daemon
from nav.eventengine.engine import EventEngine
import nav.logs
from nav.config import NAV_CONFIG

PIDFILE = 'eventengine.pid'
LOGFILE = os.path.join(NAV_CONFIG['LOG_DIR'], 'eventengine.log')
_logger = logging.getLogger(__name__)


def main():
    "main execution entry"
    options, _args = parse_options()
    nav.logs.init_stderr_logging()
    exit_if_already_running()
    if not options.foreground:
        daemonize()
    else:
        nav.daemon.writepidfile(PIDFILE)
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
        epilog=(
            "This program monitors NAV's event queue and decides which "
            "actions to take when events occur"
        ),
    )
    opt = parser.add_option
    opt(
        "-f",
        "--foreground",
        action="store_true",
        dest="foreground",
        help="run in foreground instead of daemonizing",
    )

    return parser


def exit_if_already_running():
    "Exits the process if another eventengine process is already running"
    try:
        nav.daemon.justme(PIDFILE)
    except nav.daemon.DaemonError as error:
        _logger.error(error)
        sys.exit(1)


def daemonize():
    "Daemonizes the program"
    try:
        nav.daemon.daemonize(PIDFILE, stderr=open(LOGFILE, "a"))
    except nav.daemon.DaemonError as error:
        _logger.fatal(error)
        sys.exit(1)
    install_signal_handlers()


def install_signal_handlers():
    """Installs signal handlers"""
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGHUP, sighup_handler)


def sigterm_handler(signum, _frame):
    """Logs the imminent shutdown"""
    _logger.info(
        "--- %s received: shutting down eventengine ---", nav.daemon.signame(signum)
    )
    sys.exit(0)


def sighup_handler(_signum, _frame):
    """Reopens log files."""
    _logger.info("SIGHUP received; reopening log files")
    nav.logs.reopen_log_files()
    nav.daemon.redirect_std_fds(stderr=open(LOGFILE, "a"))
    nav.logs.reset_log_levels()
    nav.logs.set_log_config()
    _logger.info("Log files reopened, log levels reloaded.")


def start_engine():
    "Starts event queue processing"
    engine = EventEngine()
    engine.start()


if __name__ == '__main__':
    main()

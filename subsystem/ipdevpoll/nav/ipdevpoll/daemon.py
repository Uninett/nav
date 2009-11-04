# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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
"""ipdevpoll daemon.

This is the daemon program that runs the IP device poller.

"""

import sys
import os
import logging, logging.config
from optparse import OptionParser

from twisted.internet import reactor

from nav import buildconf
import nav.daemon
import nav.logs

from schedule import Scheduler

pidfile = os.path.join(nav.buildconf.localstatedir, 'run', 'ipdevpolld.pid')

def run_poller():
    """Load plugins, and initiate polling schedules."""
    global scheduler
    import plugins

    plugins.import_plugins()
    scheduler = Scheduler()
    return scheduler.run()

def get_parser():
    """Setup and return a command line option parser."""
    parser = OptionParser(version="NAV " + buildconf.VERSION)
    parser.add_option("-c", "--config", dest="configfile",
                      help="read configuration from FILE", metavar="FILE")
    parser.add_option("-l", "--logconfig", dest="logconfigfile",
                      help="read logging configuration from FILE",
                      metavar="FILE")
    return parser

def init_logging():
    """Initialize ipdevpoll log system.

    Returns:

      A default logger instance to use by the daemon.

    """
    # First initialize logging to stderr.
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    formatter = logging.Formatter(log_format)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)

    root_logger = logging.getLogger('')
    root_logger.addHandler(stderr_handler)

    nav.logs.setLogLevels()

    # Now try to load config and output logs to the configured file
    # instead.
    import config
    logfile_name = config.ipdevpoll_conf.get('ipdevpoll', 'logfile')

    file_handler = logging.FileHandler(logfile_name, 'a')
    file_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.removeHandler(stderr_handler)

    return logging.getLogger('nav.ipdevpoll')

def main():
    """Main execution function"""
    parser = get_parser()
    (options, args) = parser.parse_args()

    logger = init_logging()
    logger.info("--- Starting ipdevpolld ---")

    # Check if already running
    try:
        nav.daemon.justme(pidfile)
    except nav.daemon.DaemonError, error:
        logger.error(error)
        sys.exit(1)

    # Daemonize
    try:
        nav.daemon.daemonize(pidfile,
                             stderr=nav.logs.get_logfile_from_logger())
    except nav.daemon.DaemonError, error:
        logger.error(error)
        sys.exit(1)

    nav.logs.reopen_log_files()
    logger.info("ipdevpolld now running in the background")

    reactor.callWhenRunning(run_poller)
    reactor.run()

if __name__ == '__main__':
    main()

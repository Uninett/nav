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
import logging
import signal
from optparse import OptionParser

from twisted.internet import reactor

from nav import buildconf
import nav.daemon
import nav.logs

import plugins


class IPDevPollProcess(object):
    """Main IPDevPoll process setup"""
    def __init__(self, options, args):
        self.options = options
        self.args = args
        self.logger = logging.getLogger('nav.ipdevpoll')

    def run(self):
        """Loads plugins, and initiates polling schedules."""
        # We need to react to SIGHUP and SIGTERM
        signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGTERM, self.sigterm_handler)

        plugins.import_plugins()
        # NOTE: This is locally imported because it will in turn import
        # twistedsnmp. Twistedsnmp is stupid enough to call
        # logging.basicConfig().  If imported before our own loginit, this
        # causes us to have two StreamHandlers on the root logger, duplicating
        # every log statement.
        from schedule import Scheduler
        self.scheduler = Scheduler()

        reactor.callWhenRunning(self.scheduler.run)
        reactor.run()

    def sighup_handler(self, signum, frame):
        """Reopens log files."""
        self.logger.info("SIGHUP received; reopening log files")
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(
            stderr=nav.logs.get_logfile_from_logger())
        self.logger.info("Log files reopened.")

    def sigterm_handler(self, signum, frame):
        """Cleanly shuts down logging system and the reactor."""
        self.logger.warn("SIGTERM received: Shutting down")
        logging.shutdown()
        reactor.callFromThread(reactor.stop)

class CommandProcessor(object):
    """Processes the command line and starts ipdevpoll."""
    pidfile = os.path.join(
        nav.buildconf.localstatedir, 'run', 'ipdevpolld.pid')

    def __init__(self):
        (self.options, self.args) = self.parse_options()
        self.logger = None

    def parse_options(self):
        parser = self.make_option_parser()
        (options, args) = parser.parse_args()
        return options, args

    def make_option_parser(self):
        """Sets up and returns a command line option parser."""
        parser = OptionParser(version="NAV " + buildconf.VERSION)
        parser.add_option("-c", "--config", dest="configfile",
                          help="read configuration from FILE", metavar="FILE")
        parser.add_option("-l", "--logconfig", dest="logconfigfile",
                          help="read logging configuration from FILE",
                          metavar="FILE")
        return parser

    def run(self):
        self.init_logging()
        self.logger = logging.getLogger('nav.ipdevpoll')
        self.logger.info("--- Starting ipdevpolld ---")
        self.exit_if_already_running()
        self.daemonize()
        nav.logs.reopen_log_files()
        self.logger.info("ipdevpolld now running in the background")

        self.psyco_speedup()

        self.start_ipdevpoll()

    def psyco_speedup(self):
        try:
            import psyco
        except ImportError:
            return
        from django.db import models
        psyco.cannotcompile(models.sql.query.Query.clone)
        psyco.full()


    def init_logging(self):
        """Initializes ipdevpoll logging for the current process."""
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
        if logfile_name[0] not in './':
            logfile_name = os.path.join(nav.buildconf.localstatedir,
                                        'log', logfile_name)

        file_handler = logging.FileHandler(logfile_name, 'a')
        file_handler.setFormatter(formatter)

        root_logger.addHandler(file_handler)
        root_logger.removeHandler(stderr_handler)

    def exit_if_already_running(self):
        # Check if already running
        try:
            nav.daemon.justme(self.pidfile)
        except nav.daemon.DaemonError, error:
            self.logger.error(error)
            sys.exit(1)

    def daemonize(self):
        try:
            nav.daemon.daemonize(self.pidfile,
                                 stderr=nav.logs.get_logfile_from_logger())
        except nav.daemon.DaemonError, error:
            self.logger.error(error)
            sys.exit(1)

    def start_ipdevpoll(self):
        process = IPDevPollProcess(self.options, self.args)
        process.run()

def main():
    """Main execution function"""
    processor = CommandProcessor()
    processor.run()

if __name__ == '__main__':
    main()

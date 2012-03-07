# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2012 UNINETT AS
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
import time
from optparse import OptionParser

from twisted.internet import reactor

from nav import buildconf
import nav.daemon
import nav.logs
import nav.models.manage

from . import plugins
from nav.ipdevpoll import ContextFormatter


class IPDevPollProcess(object):
    """Main IPDevPoll process setup"""
    def __init__(self, options, args):
        self.options = options
        self.args = args
        self._logger = logging.getLogger('nav.ipdevpoll')
        self._shutdown_start_time = 0

    def run(self):
        """Loads plugins, and initiates polling schedules."""
        # We need to react to SIGHUP and SIGTERM
        if not self.options.foreground:
            signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)
        signal.signal(signal.SIGUSR1, self.sigusr1_handler)

        plugins.import_plugins()
        # NOTE: This is locally imported because it will in turn import
        # twistedsnmp. Twistedsnmp is stupid enough to call
        # logging.basicConfig().  If imported before our own loginit, this
        # causes us to have two StreamHandlers on the root logger, duplicating
        # every log statement.
        from .schedule import JobScheduler

        reactor.callWhenRunning(JobScheduler.initialize_from_config_and_run,
                                self.options.onlyjob)
        reactor.addSystemEventTrigger("after", "shutdown", self.shutdown)
        reactor.run(installSignalHandlers=0)

    def sighup_handler(self, _signum, _frame):
        """Reopens log files."""
        self._logger.info("SIGHUP received; reopening log files")
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(
            stderr=nav.logs.get_logfile_from_logger())
        nav.logs.reset_log_levels()
        nav.logs.set_log_levels()
        self._logger.info("Log files reopened, log levels reloaded.")

    def sigterm_handler(self, signum, _frame):
        """Cleanly shuts down logging system and the reactor."""
        self._logger.warn("%s received: Shutting down", signame(signum))
        self._shutdown_start_time = time.time()
        reactor.callFromThread(reactor.stop)

    def sigusr1_handler(self, _signum, _frame):
        "Log list of active jobs on SIGUSR1"
        self._logger.info("SIGUSR1 received: Logging active jobs")
        from nav.ipdevpoll.schedule import JobScheduler
        JobScheduler.log_active_jobs(logging.INFO)

    def shutdown(self):
        """Initiates a shutdown sequence"""
        self._log_shutdown_time()
        logging.shutdown()

    def _log_shutdown_time(self):
        sequence_time = time.time() - self._shutdown_start_time
        self._logger.warn("Shutdown sequence completed in %.02f seconds",
                          sequence_time)


class CommandProcessor(object):
    """Processes the command line and starts ipdevpoll."""
    pidfile = os.path.join(
        nav.buildconf.localstatedir, 'run', 'ipdevpolld.pid')

    def __init__(self):
        (self.options, self.args) = self.parse_options()
        self._logger = None

    def parse_options(self):
        """Parses the command line options"""
        parser = self.make_option_parser()
        (options, args) = parser.parse_args()
        if options.logstderr and not options.foreground:
            parser.error('-s is only valid if running in foreground')

        return options, args

    def make_option_parser(self):
        """Sets up and returns a command line option parser."""
        parser = OptionParser(
            version="NAV " + buildconf.VERSION,
            epilog="This program runs SNMP polling jobs for IP devices "
            "monitored by NAV")
        opt = parser.add_option
        opt("-f", "--foreground", action="store_true", dest="foreground",
            help="run in foreground instead of daemonizing")
        opt("-s", "--log-stderr", action="store_true", dest="logstderr",
            help="log to stderr instead of log file")
        opt("-j", "--list-jobs", action="callback", callback=self._list_jobs,
            help="print a list of configured jobs and exit")
        opt("-p", "--list-plugins", action="callback",
            callback=self._list_plugins,
            help="load and print a list of configured plugins")
        opt("-J", action="store", dest="onlyjob", choices=self._joblist(),
            metavar="JOBNAME", help="run only JOBNAME in this process")
        return parser

    def run(self):
        """Runs an ipdevpoll process"""
        self.init_logging(self.options.logstderr)
        self._logger = logging.getLogger('nav.ipdevpoll')
        self._logger.info("--- Starting ipdevpolld ---")
        if not self.options.foreground:
            self.exit_if_already_running()
            self.daemonize()
            nav.logs.reopen_log_files()
            self._logger.info("ipdevpolld now running in the background")

        self.start_ipdevpoll()

    @staticmethod
    def init_logging(stderr_only=False):
        """Initializes ipdevpoll logging for the current process."""
        formatter = ContextFormatter()

        # First initialize logging to stderr.
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)

        root_logger = logging.getLogger('')
        root_logger.addHandler(stderr_handler)

        nav.logs.set_log_levels()

        if not stderr_only:
            # Now try to load config and output logs to the configured file
            # instead.
            from nav.ipdevpoll import config
            logfile_name = config.ipdevpoll_conf.get('ipdevpoll', 'logfile')
            if logfile_name[0] not in './':
                logfile_name = os.path.join(nav.buildconf.localstatedir,
                                            'log', logfile_name)

            file_handler = logging.FileHandler(logfile_name, 'a')
            file_handler.setFormatter(formatter)

            root_logger.addHandler(file_handler)
            root_logger.removeHandler(stderr_handler)
            nav.daemon.redirect_std_fds(
                stderr=nav.logs.get_logfile_from_logger())

    def exit_if_already_running(self):
        """Exits the process if another ipdevpoll daemon is already running"""
        try:
            nav.daemon.justme(self.pidfile)
        except nav.daemon.DaemonError, error:
            self._logger.error(error)
            sys.exit(1)

    def daemonize(self):
        """Puts the ipdevpoll process in the background"""
        try:
            nav.daemon.daemonize(self.pidfile,
                                 stderr=nav.logs.get_logfile_from_logger())
        except nav.daemon.DaemonError, error:
            self._logger.error(error)
            sys.exit(1)

    def start_ipdevpoll(self):
        """Creates an ipdevpoll process and runs it"""
        process = IPDevPollProcess(self.options, self.args)
        process.run()

    @staticmethod
    def _joblist():
        from nav.ipdevpoll.config import get_jobs
        jobs = sorted(job.name for job in get_jobs())
        return jobs

    @staticmethod
    def _list_jobs(*_args, **_kwargs):
        from nav.ipdevpoll.config import get_jobs
        jobs = sorted(job.name for job in get_jobs())
        print '\n'.join(jobs)
        sys.exit()

    @staticmethod
    def _list_plugins(*_args, **_kwargs):
        plugins.import_plugins()
        print '\n'.join(sorted(plugins.plugin_registry.keys()))
        sys.exit()

def signame(signum):
    """Looks up signal name from signal number"""
    lookup = dict((num, name) for name, num in vars(signal).items()
                  if name.startswith('SIG'))
    return lookup.get(signum, signum)

def main():
    """Main execution function"""
    processor = CommandProcessor()
    processor.run()

if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2012 Uninett AS
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
"""ipdevpoll daemon.

This is the daemon program that runs the IP device poller.

"""

import sys
import os
import logging
from multiprocessing import cpu_count
import signal
import time
import argparse

import twisted
from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred, setDebugging
from twisted.python.failure import Failure

from nav import buildconf
from nav.config import NAV_CONFIG
from nav.util import is_valid_ip
import nav.daemon
from nav.daemon import signame
import nav.logs
from nav.models import manage

from nav.ipdevpoll import ContextFormatter, schedule, db
from . import plugins, pool


class NetboxAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if not values:
            parser.error("%s argument must be non-empty" % option_string)

        search_base = manage.Netbox.objects.select_related(
            'type', 'type__vendor'
        ).order_by('sysname')
        if is_valid_ip(values, strict=True):
            matches = search_base.filter(ip=values)
        else:
            matches = search_base.filter(sysname__startswith=values)

        if len(matches) == 1:
            namespace.netbox = matches[0]
            namespace.foreground = True
            namespace.logstderr = True
            return
        elif len(matches) > 1:
            print("matched more than one netbox:")
            print('\n'.join("%s (%s)" % (n.sysname, n.ip) for n in matches))
        else:
            print("no netboxes match %r" % values)

        sys.exit(1)


class IPDevPollProcess(object):
    """Main IPDevPoll process setup"""

    def __init__(self, options):
        self.options = options
        self._logger = logging.getLogger('nav.ipdevpoll')
        self._shutdown_start_time = 0
        self.job_loggers = []
        self.reloaders = []

    def run(self):
        """Loads plugins, and initiates polling schedules."""
        reactor.callWhenRunning(self.install_sighandlers)

        if self.options.netbox:
            self.setup_single_job()
        elif self.options.multiprocess:
            self.setup_multiprocess(self.options.multiprocess, self.options.max_jobs)
        elif self.options.worker:
            self.setup_worker()
        else:
            self.setup_scheduling()

        reactor.suggestThreadPoolSize(self.options.threadpoolsize)
        reactor.addSystemEventTrigger("after", "shutdown", self.shutdown)
        reactor.run()

    def install_sighandlers(self):
        "Installs ipdevpoll's own signal handlers"
        if not self.options.foreground:
            signal.signal(signal.SIGHUP, self.sighup_handler)
        signal.signal(signal.SIGTERM, self.sigterm_handler)
        signal.signal(signal.SIGINT, self.sigterm_handler)
        signal.signal(signal.SIGUSR1, self.sigusr1_handler)
        signal.signal(signal.SIGUSR2, self.sigusr2_handler)

    def setup_scheduling(self):
        "Sets up regular job scheduling according to config"
        # NOTE: This is locally imported because it will in turn import
        # twistedsnmp. Twistedsnmp is stupid enough to call
        # logging.basicConfig().  If imported before our own loginit, this
        # causes us to have two StreamHandlers on the root logger, duplicating
        # every log statement.
        self._logger.info("Starting scheduling in single process")
        from .schedule import JobScheduler

        plugins.import_plugins()
        self.work_pool = pool.InlinePool()
        reactor.callWhenRunning(
            JobScheduler.initialize_from_config_and_run,
            self.work_pool,
            self.options.onlyjob,
        )
        db.delete_stale_job_refresh_notifications()
        reactor.callWhenRunning(
            db.subscribe_to_event_notifications, schedule.handle_incoming_events
        )

        def log_scheduler_jobs():
            JobScheduler.log_active_jobs(logging.INFO)

        self.job_loggers.append(log_scheduler_jobs)

        def reload_netboxes():
            JobScheduler.reload()

        self.reloaders.append(reload_netboxes)

    def setup_worker(self):
        "Sets up a worker process"
        # NOTE: This is locally imported because it will in turn import
        # twistedsnmp. Twistedsnmp is stupid enough to call
        # logging.basicConfig().  If imported before our own loginit, this
        # causes us to have two StreamHandlers on the root logger, duplicating
        # every log statement.
        self._logger.info("Starting worker process")
        plugins.import_plugins()

        def init():
            handler = pool.initialize_worker()
            self.job_loggers.append(handler.log_jobs)

        reactor.callWhenRunning(init)

    def setup_single_job(self):
        "Sets up a single job run with exit when done"
        from .jobs import JobHandler
        from . import config

        def _run_job():
            descriptors = dict((d.name, d) for d in config.get_jobs())
            job = descriptors[self.options.onlyjob]
            self._log_context = dict(job=job.name, sysname=self.options.netbox.sysname)
            job_handler = JobHandler(
                job.name,
                self.options.netbox.id,
                plugins=job.plugins,
                interval=job.interval,
            )
            deferred = maybeDeferred(job_handler.run)
            deferred.addBoth(_log_job, job_handler, interval=job.interval)
            deferred.addBoth(lambda x: reactor.stop())

        def _log_job(result, handler, interval):
            success = not isinstance(result, Failure)
            schedule.log_job_externally(handler, success if result else None, interval)

        plugins.import_plugins()
        self._logger.info(
            "Running single %r job for %s", self.options.onlyjob, self.options.netbox
        )
        reactor.callWhenRunning(_run_job)

    def setup_multiprocess(self, process_count, max_jobs):
        self._logger.info("Starting multi-process setup")
        from .schedule import JobScheduler

        plugins.import_plugins()
        self.work_pool = pool.WorkerPool(
            process_count, max_jobs, self.options.threadpoolsize
        )
        reactor.callWhenRunning(
            JobScheduler.initialize_from_config_and_run,
            self.work_pool,
            self.options.onlyjob,
        )
        db.delete_stale_job_refresh_notifications()
        reactor.callWhenRunning(
            db.subscribe_to_event_notifications, schedule.handle_incoming_events
        )

        def log_scheduler_jobs():
            JobScheduler.log_active_jobs(logging.INFO)

        self.job_loggers.append(log_scheduler_jobs)
        self.job_loggers.append(self.work_pool.log_summary)

        def reload_netboxes():
            JobScheduler.reload()

        self.reloaders.append(reload_netboxes)

    def sighup_handler(self, _signum, _frame):
        """Reopens log files."""
        self._logger.info("SIGHUP received; reopening log files")
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(stderr=nav.logs.get_logfile_from_logger())
        nav.logs.reset_log_levels()
        nav.logs.set_log_config()
        self._logger.info("Log files reopened, log levels reloaded.")

    def sigterm_handler(self, signum, _frame):
        """Cleanly shuts down logging system and the reactor."""
        self._logger.warning("%s received: Shutting down", signame(signum))
        self._shutdown_start_time = time.time()
        reactor.callFromThread(reactor.stop)

    def sigusr1_handler(self, _signum, _frame):
        "Log list of active jobs on SIGUSR1"
        self._logger.info("SIGUSR1 received: Logging active jobs")
        for logger in self.job_loggers:
            logger()

    def sigusr2_handler(self, _signum, _frame):
        "Reload boxes from database"
        self._logger.info("SIGUSR2 received: Reloading netboxes")
        for reloader in self.reloaders:
            reloader()

    def shutdown(self):
        """Initiates a shutdown sequence"""
        self._log_shutdown_time()
        logging.shutdown()

    def _log_shutdown_time(self):
        if self._shutdown_start_time > 0:
            sequence_time = time.time() - self._shutdown_start_time
            self._logger.warning(
                "Shutdown sequence completed in %.02f seconds", sequence_time
            )


class CommandProcessor(object):
    """Processes the command line and starts ipdevpoll."""

    pidfile = 'ipdevpolld.pid'

    def __init__(self):
        self.options = self.parse_options()
        self._logger = None

    def parse_options(self):
        """Parses the command line options"""
        parser = self.make_option_parser()
        options = parser.parse_args()
        if options.list_jobs:
            self._list_jobs()
        if options.list_plugins:
            self._list_plugins()
        if options.logstderr and not options.foreground:
            parser.error('-s is only valid if running in foreground')
        if options.netbox and not options.onlyjob:
            parser.error('specifying a netbox requires the -J option')
        if options.multiprocess:
            options.pidlog = True
        if options.capture_vars:
            setDebugging(True)
        if options.multiprocess and options.multiprocess < 2:
            parser.error('--multiprocess requires at least 2 workers')

        return options

    def make_option_parser(self):
        """Sets up and returns a command line option parser."""
        parser = argparse.ArgumentParser(
            epilog="This program runs SNMP polling jobs for IP devices monitored by NAV"
        )
        opt = parser.add_argument

        opt('--version', action='version', version='NAV ' + buildconf.VERSION)
        opt(
            "-f",
            "--foreground",
            action="store_true",
            dest="foreground",
            help="run in foreground instead of daemonizing",
        )
        opt(
            "-s",
            "--log-stderr",
            action="store_true",
            dest="logstderr",
            help="log to stderr instead of log file",
        )
        opt(
            "-j",
            "--list-jobs",
            action="store_true",
            help="print a list of configured jobs and exit",
        )
        opt(
            "-p",
            "--list-plugins",
            action="store_true",
            help="load and print a list of configured plugins",
        )
        opt(
            "-J",
            action="store",
            dest="onlyjob",
            choices=self._joblist(),
            metavar="JOBNAME",
            help="run only JOBNAME jobs in this process",
        )
        opt(
            "-n",
            "--netbox",
            action=NetboxAction,
            metavar="NETBOX",
            help="Run JOBNAME once for NETBOX. Also implies -f and -s options.",
        )
        opt(
            "-m",
            "--multiprocess",
            type=int,
            dest="multiprocess",
            nargs='?',
            const=cpu_count(),
            metavar='WORKERS',
            help="Run ipdevpoll in a multiprocess setup. If WORKERS is not set "
            "it will default to number of cpus in the system",
        )
        opt(
            "-M",
            "--max-jobs-per-worker",
            type=int,
            dest="max_jobs",
            metavar="JOBS",
            help="Restart worker processes after completing "
            "JOBS jobs. (Default: Don't restart)",
        )
        opt(
            "-P",
            "--pidlog",
            action="store_true",
            dest="pidlog",
            help="Include process ID in every log line",
        )
        opt(
            "--capture-vars",
            action="store_true",
            dest="capture_vars",
            help="Capture and print locals and globals in tracebacks when "
            "debug logging",
        )
        opt(
            "-c",
            "--clean",
            action="store_true",
            dest="clean",
            help="cleans/purges old job log entries from the database and then exits",
        )
        opt(
            "--threadpoolsize",
            action="store",
            dest="threadpoolsize",
            metavar="COUNT",
            type=int,
            default=10,
            help="the number of database worker threads, and thus db "
            "connections, to use in this process",
        )
        opt(
            "--worker",
            action="store_true",
            help="Used internally when lauching worker processes",
        )
        return parser

    def run(self):
        """Runs an ipdevpoll process"""
        self.init_logging(self.options.logstderr)
        self._logger = logging.getLogger('nav.ipdevpoll')

        if self.options.clean:
            self._logger.debug("purging old job log entries")
            db.purge_old_job_log_entries()
            sys.exit(0)
        if self.options.multiprocess:
            self._logger.info("--- Starting ipdevpolld multiprocess master ---")
        elif self.options.onlyjob:
            self._logger.info("--- Starting ipdevpolld %s ---", self.options.onlyjob)
        else:
            self._logger.info("--- Starting ipdevpolld ---")

        if not self.options.foreground:
            self.exit_if_already_running()
            self.daemonize()
            nav.logs.reopen_log_files()
            self._logger.info("ipdevpolld now running in the background")

        self.start_ipdevpoll()

    def init_logging(self, stderr_only=False):
        """Initializes ipdevpoll logging for the current process."""
        observer = twisted.python.log.PythonLoggingObserver()
        observer.start()

        formatter = ContextFormatter(self.options.pidlog)

        logfile_name = None
        if not stderr_only:
            # Now try to load config and output logs to the configured file
            # instead.
            from nav.ipdevpoll import config

            logfile_name = config.ipdevpoll_conf.get('ipdevpoll', 'logfile')
            if not logfile_name.startswith(os.sep):
                logfile_name = os.path.join(NAV_CONFIG['LOG_DIR'], logfile_name)

        nav.logs.init_generic_logging(
            logfile=logfile_name,
            stderr=stderr_only,
            formatter=formatter,
            read_config=True,
        )

        if not stderr_only:
            nav.daemon.redirect_std_fds(stderr=nav.logs.get_logfile_from_logger())

    def exit_if_already_running(self):
        """Exits the process if another ipdevpoll daemon is already running"""
        try:
            nav.daemon.justme(self.pidfile)
        except nav.daemon.DaemonError as error:
            self._logger.error(error)
            sys.exit(1)

    def daemonize(self):
        """Puts the ipdevpoll process in the background"""
        try:
            nav.daemon.daemonize(
                self.pidfile, stderr=nav.logs.get_logfile_from_logger()
            )
        except nav.daemon.DaemonError as error:
            self._logger.error(error)
            sys.exit(1)

    def start_ipdevpoll(self):
        """Creates an ipdevpoll process and runs it"""
        process = IPDevPollProcess(self.options)
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
        print('\n'.join(jobs))
        sys.exit()

    @staticmethod
    def _list_plugins(*_args, **_kwargs):
        plugins.import_plugins()
        print('\n'.join(sorted(plugins.plugin_registry.keys())))
        sys.exit()


def main():
    """Main execution function"""
    processor = CommandProcessor()
    processor.run()


if __name__ == '__main__':
    main()

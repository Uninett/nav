# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2011 UNINETT AS
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
"""Handle scheduling of polling jobs."""

import logging
import datetime
from operator import itemgetter
from random import randint

from twisted.internet import task, threads

from nav import ipdevpoll
import shadows
import config
import signals
from dataloader import NetboxLoader
from jobs import JobHandler, AbortedJobError
from nav.tableformat import SimpleTableFormatter

from nav.ipdevpoll.utils import log_unhandled_failure

logger = logging.getLogger(__name__)

class NetboxJobScheduler(object):
    """Netbox job schedule handler.

    An instance of this class takes care of scheduling, running and
    rescheduling of a single JobHandler for a single netbox.

    """

    def __init__(self, job, netbox):
        self.job = job
        self.netbox = netbox
        self.logger = \
            ipdevpoll.get_instance_logger(self, "%s.(%s)" %
                                          (self.job.name, netbox.sysname))
        self.cancelled = False
        self.job_handler = None
        self.loop = None

    def start(self):
        """Start polling schedule."""
        self.loop = task.LoopingCall(self.run_job)
        deferred = self.loop.start(interval=self.job.interval, now=True)
        return deferred

    def cancel(self):
        """Cancel scheduling of this job for this box.

        Future runs will not be scheduled after this."""
        if self.loop.running:
            self.loop.stop()
            self.cancelled = True
            self.logger.debug("cancel: Job %r cancelled for %s",
                              self.job.name, self.netbox.sysname)
            self.cancel_running_job()
        else:
            self.logger.debug("cancel: Job %r already cancelled for %s",
                              self.job.name, self.netbox.sysname)

    def cancel_running_job(self):
        if self.job_handler:
            self.job_handler.cancel()

    def run_job(self, dummy=None):
        if self.is_running():
            self.logger.info("Previous %r job is still running for %s, "
                             "not running again now.",
                             self.job.name, self.netbox.sysname)
        else:
            # We're ok to start a polling run.
            job_handler = JobHandler(self.job.name, self.netbox,
                                     plugins=self.job.plugins)
            self.job_handler = job_handler

            deferred = job_handler.run()
            deferred.addErrback(self._reschedule)
            deferred.addErrback(self._log_unhandled_error)

            deferred.addCallback(self._unregister_handler)
            deferred.addCallback(self._log_time_to_next_run)


    def is_running(self):
        return self.job_handler is not None

    def _reschedule(self, failure):
        """Examines the job failure and reschedules the job if needed."""
        failure.trap(AbortedJobError)
        if self.loop.running:
            # FIXME: Should be configurable per. job
            delay = randint(5*60, 10*60) # within 5-10 minutes
            self.logger.info("Rescheduling %r for %s in %d seconds",
                             self.job.name, self.netbox.sysname, delay)
            self.loop.call.reset(delay)

    def _log_unhandled_error(self, failure):
        log_unhandled_failure(self.logger,
                              failure,
                              "Unhandled exception raised by JobHandler")
        return failure

    def _unregister_handler(self, result):
        """Remove a JobHandler from internal data structures."""
        if self.job_handler:
            self.job_handler = None
        return result

    def _log_time_to_next_run(self, thing=None):
        if self.loop.running and self.loop.call is not None:
            next_time = \
                datetime.datetime.fromtimestamp(self.loop.call.getTime())
            self.logger.debug("Next %r job for %s will be at %s",
                              self.job.name, self.netbox.sysname, next_time)
        return thing


class JobScheduler(object):
    active_schedulers = set()
    job_logging_loop = None

    def __init__(self, job):
        """Initializes a job schedule from the job descriptor."""
        self._logger = ipdevpoll.get_instance_logger(self, job.name)
        self.job = job
        self.netboxes = NetboxLoader()
        self.active_netboxes = {}

        self.active_schedulers.add(self)

    @classmethod
    def initialize_from_config_and_run(cls):
        descriptors = config.get_jobs()
        schedulers = [JobScheduler(d) for d in descriptors]
        for scheduler in schedulers:
            scheduler.run()

    def run(self):
        """Initiate scheduling of this job."""
        signals.netbox_type_changed.connect(self.on_netbox_type_changed)
        self._setup_active_job_logging()
        self.netbox_reload_loop = task.LoopingCall(self._reload_netboxes)
        # FIXME: Interval should be configurable
        deferred = self.netbox_reload_loop.start(interval=2*60.0, now=True)
        return deferred

    def on_netbox_type_changed(self, netbox_id, new_type, **kwargs):
        """Performs various cleanup and reload actions on a netbox type change
        signal.

        The netbox' data are cleaned up, and the next netbox data reload is
        scheduled to take place immediately.

        """
        sysname = netbox_id in self.netboxes and \
            self.netboxes[netbox_id].sysname or str(netbox_id)
        self._logger.info("Cancelling all jobs for %s due to type change.",
                          sysname)
        self.cancel_netbox_scheduler(netbox_id)
        def reset(_):
            self.netbox_reload_loop.call.reset(1)
        df = threads.deferToThread(shadows.Netbox.cleanup_replaced_netbox,
                                   netbox_id, new_type)
        df.addCallback(reset)
        return df

    def _setup_active_job_logging(self):
        if self.__class__.job_logging_loop is None:
            loop = task.LoopingCall(self.__class__._log_active_jobs)
            self.__class__.job_logging_loop = loop
            loop.start(interval=5*60.0, now=False)

    def _reload_netboxes(self):
        """Reload the set of netboxes to poll and update schedules."""
        deferred = self.netboxes.load_all()
        deferred.addCallback(self._process_reloaded_netboxes)
        return deferred

    def _process_reloaded_netboxes(self, result):
        """Process the result of a netbox reload and update schedules."""
        (new_ids, removed_ids, changed_ids) = result

        # Deschedule removed and changed boxes
        for netbox_id in removed_ids.union(changed_ids):
            self.cancel_netbox_scheduler(netbox_id)

        # Schedule new and changed boxes
        for netbox_id in new_ids.union(changed_ids):
            self.add_netbox_scheduler(netbox_id)

    def add_netbox_scheduler(self, netbox_id):
        netbox = self.netboxes[netbox_id]
        scheduler = NetboxJobScheduler(self.job, netbox)
        self.active_netboxes[netbox_id] = scheduler
        return scheduler.start()

    def cancel_netbox_scheduler(self, netbox_id):
        if netbox_id not in self.active_netboxes:
            return
        scheduler = self.active_netboxes[netbox_id]
        scheduler.cancel()
        del self.active_netboxes[netbox_id]

    @classmethod
    def _log_active_jobs(cls):
        """Debug logs a list of running job handlers.

        The handlers will be sorted by descending runtime.

        """
        jobs = [(netbox_scheduler.netbox.sysname,
                 netbox_scheduler.job.name,
                 netbox_scheduler.job_handler.get_current_runtime())
                for scheduler in cls.active_schedulers
                for netbox_scheduler in scheduler.active_netboxes.values()
                if netbox_scheduler.is_running()]
        jobs.sort(key=itemgetter(2), reverse=True)
        table_formatter = SimpleTableFormatter(jobs)

        logger = ipdevpoll.get_class_logger(cls)
        if jobs:
            logger.debug("currently active jobs (%d):\n%s",
                         len(jobs), table_formatter)
        else:
            logger.debug("no currently active jobs")


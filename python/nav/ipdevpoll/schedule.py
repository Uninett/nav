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
import time
from operator import itemgetter
from random import randint

from twisted.internet import task, threads, reactor
from twisted.internet.defer import Deferred

from nav import ipdevpoll
import shadows
import config
import signals
from dataloader import NetboxLoader
from jobs import JobHandler, AbortedJobError
from nav.tableformat import SimpleTableFormatter

from nav.ipdevpoll.utils import log_unhandled_failure

_logger = logging.getLogger(__name__)

class NetboxJobScheduler(object):
    """Netbox job schedule handler.

    An instance of this class takes care of scheduling, running and
    rescheduling of a single JobHandler for a single netbox.

    """
    job_counters = {}
    job_queues = {}

    def __init__(self, job, netbox):
        self.job = job
        self.netbox = netbox
        self._logger = ipdevpoll.get_context_logger(self,
                                                    job=self.job.name,
                                                    sysname=netbox.sysname)
        self.cancelled = False
        self.job_handler = None
        self._deferred = Deferred()
        self._next_call = None
        self._last_job_started_at = 0

    def start(self):
        """Start polling schedule."""
        self._next_call = reactor.callLater(0, self.run_job)
        return self._deferred

    def cancel(self):
        """Cancel scheduling of this job for this box.

        Future runs will not be scheduled after this."""
        if self._next_call.active():
            self._next_call.cancel()
            self.cancelled = True
            self._logger.debug("cancel: Job %r cancelled for %s",
                               self.job.name, self.netbox.sysname)
            self.cancel_running_job()
        else:
            self._logger.debug("cancel: Job %r already cancelled for %s",
                               self.job.name, self.netbox.sysname)
        self._deferred.callback(self)

    def cancel_running_job(self):
        if self.job_handler:
            self.job_handler.cancel()

    def run_job(self, dummy=None):
        if self.is_running():
            self._logger.info("Previous %r job is still running for %s, "
                              "not running again now.",
                              self.job.name, self.netbox.sysname)
            return

        if self.is_job_limit_reached():
            self._logger.debug("intensity limit for %r reached - waiting to "
                               "run for %s", self.job.name, self.netbox.sysname)
            self.queue_myself()
            return

        # We're ok to start a polling run.
        job_handler = JobHandler(self.job.name, self.netbox,
                                 plugins=self.job.plugins)
        self.job_handler = job_handler
        self.count_job()
        self._last_job_started_at = time.time()

        deferred = job_handler.run()
        deferred.addCallbacks(self._reschedule_on_success,
                              self._reschedule_on_failure)
        deferred.addErrback(self._log_unhandled_error)

        deferred.addCallback(self._unregister_handler)
        deferred.addCallback(self._log_time_to_next_run)


    def is_running(self):
        return self.job_handler is not None

    def _reschedule_on_success(self, result):
        """Reschedules the next normal run of this job."""
        time_passed = time.time() - self._last_job_started_at
        delay = max(0, self.job.interval - time_passed)
        self.reschedule(delay)
        return result

    def _reschedule_on_failure(self, failure):
        """Examines the job failure and reschedules the job if needed."""
        failure.trap(AbortedJobError)
        # FIXME: Should be configurable per. job
        delay = randint(5*60, 10*60) # within 5-10 minutes
        self.reschedule(delay)

    def reschedule(self, delay):
        """Reschedules the next run of of this job"""
        self._logger.info("Rescheduling %r for %s in %d seconds",
                          self.job.name, self.netbox.sysname, delay)

        if self._next_call.active():
            self._next_call.reset(delay)
        else:
            self._next_call = reactor.callLater(delay, self.run_job)


    def _log_unhandled_error(self, failure):
        log_unhandled_failure(self._logger,
                              failure,
                              "Unhandled exception raised by JobHandler")

    def _unregister_handler(self, result):
        """Remove a JobHandler from internal data structures."""
        if self.job_handler:
            self.job_handler = None
            self.uncount_job()
            self.unqueue_next_job()
        return result

    def _log_time_to_next_run(self, thing=None):
        if self._next_call and self._next_call.active():
            next_time = datetime.datetime.fromtimestamp(
                self._next_call.getTime())
            self._logger.info("Next %r job for %s will be at %s",
                              self.job.name, self.netbox.sysname, next_time)
        return thing

    def count_job(self):
        current_count = self.__class__.job_counters.get(self.job.name, 0)
        current_count += 1
        self.__class__.job_counters[self.job.name] = current_count

    def uncount_job(self):
        current_count = self.__class__.job_counters.get(self.job.name, 0)
        current_count -= 1
        self.__class__.job_counters[self.job.name] = max(current_count, 0)

    def get_job_count(self):
        return self.__class__.job_counters.get(self.job.name, 0)

    def is_job_limit_reached(self):
        """Returns True if the number of jobs >= the intensity setting.

        Only jobs of the same name as this one is considered.

        """
        return (self.job.intensity > 0 and
                self.get_job_count() >= self.job.intensity)

    def queue_myself(self):
        self.get_job_queue().append(self)

    def unqueue_next_job(self):
        queue = self.get_job_queue()
        if not self.is_job_limit_reached() and len(queue) > 0:
            handler = queue.pop(0)
            return handler.start()

    def get_job_queue(self):
        if self.job.name not in self.job_queues:
            self.job_queues[self.job.name] = []
        return self.job_queues[self.job.name]

class JobScheduler(object):
    active_schedulers = set()
    job_logging_loop = None

    def __init__(self, job):
        """Initializes a job schedule from the job descriptor."""
        self._logger = ipdevpoll.get_context_logger(self, job=job.name)
        self.job = job
        self.netboxes = NetboxLoader(context=dict(job=job.name))
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

        logger = logging.getLogger("%s.joblist" % __name__)
        if jobs:
            logger.debug("currently active jobs (%d):\n%s",
                         len(jobs), table_formatter)
        else:
            logger.debug("no active jobs (%d JobHandlers)",
                         JobHandler.get_instance_count())

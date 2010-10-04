# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 UNINETT AS
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

from twisted.internet import task, threads

from nav import ipdevpoll
import shadows
import config
import signals
from dataloader import NetboxLoader
from jobs import JobHandler, AbortedJobError
from nav.tableformat import SimpleTableFormatter

logger = logging.getLogger(__name__)

class NetboxScheduler(object):
    """Netbox job schedule handler.

    An instance of this class takes care of scheduling, running and
    rescheduling of a single JobHandler for a single netbox.

    """

    running_job_map = {}
    """A map of running jobs for Netboxes.

    Scheduling will not allow simultaneous runs of the same job against the same
    Netbox.

      {netbox: [JobHandler, JobHandler...]}

    """

    DEFAULT_INTERVAL = 3600.0 # seconds


    def __init__(self, jobname, netbox, interval=None, plugins=None):
        self.jobname = jobname
        self.netbox = netbox
        self.logger = \
            ipdevpoll.get_instance_logger(self, "%s.(%s)" % 
                                          (self.jobname, netbox.sysname))

        self.plugins = plugins or []
        self.interval = interval or self.DEFAULT_INTERVAL
        self.cancelled = False

    def start(self):
        """Start polling schedule."""
        self.loop = task.LoopingCall(self.run_job)
        deferred = self.loop.start(interval=self.interval, now=True)
        return deferred

    def cancel(self):
        """Cancel scheduling of this job for this box.

        Future runs will not be scheduled after this."""
        if self.loop.running:
            self.loop.stop()
            self.cancelled = True
            self.logger.debug("cancel: Job %r cancelled for %s",
                              self.jobname, self.netbox.sysname)
        else:
            self.logger.debug("cancel: Job %r already cancelled for %s",
                              self.jobname, self.netbox.sysname)

    def _map_cleanup(self, result, job_handler):
        """Remove a JobHandler from internal data structures."""
        handlers = self._get_running_job_handlers()
        if job_handler in handlers:
            handlers.remove(job_handler)
        if self.job_handler:
            self.job_handler = None
        return result

    def run_job(self, dummy=None):
        if self._is_this_job_already_running():
            self.logger.info("Previous %r job is still running for %s, "
                             "not running again now.",
                             self.jobname, self.netbox.sysname)
        else:
            # We're ok to start a polling run.
            job_handler = JobHandler(self.jobname, self.netbox, 
                                     plugins=self.plugins)
            self.job_handler = job_handler
            self._register_running_job(job_handler)

            deferred = job_handler.run()
            deferred.addErrback(self._reschedule)
            deferred.addErrback(self._log_unhandled_error, job_handler)

            deferred.addCallback(self._map_cleanup, job_handler)
            deferred.addCallback(self._log_time_to_next_run)

    def _is_this_job_already_running(self):
        handlers = self._get_running_job_handlers()
        handler_names = [h.name for h in handlers]
        return self.jobname in handler_names

    def _is_some_job_running(self):
        return bool(NetboxScheduler.running_job_map.get(self.netbox, False))

    def _get_running_job_handlers(self):
        return NetboxScheduler.running_job_map.get(self.netbox, set())

    def _register_running_job(self, job_handler):
        handlers = self._get_running_job_handlers()
        handlers.add(job_handler)
        self.running_job_map[self.netbox] = handlers

    def _reschedule(self, failure):
        """Examines the job failure and reschedules the job if needed."""
        failure.trap(AbortedJobError)
        if self.loop.running:
            delay = 60
            self.logger.info("Rescheduling %r for %s in %d seconds",
                             self.jobname, self.netbox.sysname, delay)
            self.loop.call.reset(delay)

    def _log_unhandled_error(self, failure, job_handler):
        self.logger.error(
            "Unhandled exception raised by JobHandler: %s\n%s",
            failure.getErrorMessage(),
            failure.getTraceback()
            )
        return failure

    def _log_time_to_next_run(self, thing=None):
        if self.loop.running and self.loop.call is not None:
            next_time = \
                datetime.datetime.fromtimestamp(self.loop.call.getTime())
            self.logger.debug("Next %r job for %s will be at %s",
                              self.jobname, self.netbox.sysname, next_time)
        return thing

    @classmethod
    def _log_active_jobs(cls):
        """Debug logs a list of running jobs.

        The jobs will be sorted by descending runtime.

        """
        jobs = [(box.sysname, job.name, job.get_current_runtime())
                for box in cls.running_job_map.keys()
                for job in cls.running_job_map[box]]
        jobs.sort(key=itemgetter(2), reverse=True)
        table_formatter = SimpleTableFormatter(jobs)

        logger = ipdevpoll.get_class_logger(cls)
        if jobs:
            logger.debug("currently active jobs (%d):\n%s",
                         len(jobs), table_formatter)
        else:
            logger.debug("no currently active jobs")



class Scheduler(object):
    """Controller of the polling schedule.

    A scheduler allocates individual job schedules for each netbox.
    It will reload the list of netboxes from the database at set
    intervals; any netbox removed from the database will have its jobs
    descheduled, while new netboxes that appear will be scheduled
    immediately.

    There should only be one single Scheduler instance in an ipdevpoll
    process, although a singleton pattern will not be enforced by this
    class.

    """
    def __init__(self):
        self._logger = ipdevpoll.get_instance_logger(self, id(self))
        self.netboxes = NetboxLoader()
        self.netbox_schedulers_map = {}

    def run(self):
        """Initiate scheduling of polling."""
        signals.netbox_type_changed.connect(self.on_netbox_type_changed)
        self.netbox_reload_loop = task.LoopingCall(self.reload_netboxes)
        # FIXME: Interval should be configurable
        deferred = self.netbox_reload_loop.start(interval=2*60.0, now=True)
        return deferred

    def reload_netboxes(self):
        """Reload the set of netboxes to poll and update schedules."""
        deferred = self.netboxes.load_all()
        deferred.addCallback(self.process_reloaded_netboxes)
        return deferred

    def process_reloaded_netboxes(self, result):
        """Process the result of a netbox reload and update schedules."""
        (new_ids, removed_ids, changed_ids) = result

        # Deschedule removed and changed boxes
        for netbox_id in removed_ids.union(changed_ids):
            self.cancel_netbox_schedulers(netbox_id)

        # Schedule new and changed boxes
        for netbox_id in new_ids.union(changed_ids):
            self.add_netbox_schedulers(netbox_id)

    def add_netbox_schedulers(self, netbox_id):
        for jobname,(interval, plugins) in config.get_jobs().items():
            self.add_netbox_scheduler(jobname, netbox_id, interval, plugins)
            
    def add_netbox_scheduler(self, jobname, netbox_id, interval, plugins):
        netbox = self.netboxes[netbox_id]
        scheduler = NetboxScheduler(jobname, netbox, interval, plugins)

        if netbox.id not in self.netbox_schedulers_map:
            self.netbox_schedulers_map[netbox.id] = [scheduler]
        else:
            self.netbox_schedulers_map[netbox.id].append(scheduler)
        return scheduler.start()

    def cancel_netbox_schedulers(self, netbox_id):
        if netbox_id in self.netbox_schedulers_map:
            schedulers = self.netbox_schedulers_map[netbox_id]
            for scheduler in schedulers:
                scheduler.cancel()
            del self.netbox_schedulers_map[netbox_id]
            return len(schedulers)
        else:
            return 0

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
        self.cancel_netbox_schedulers(netbox_id)
        def reset(_):
            self.netbox_reload_loop.call.reset(1)
        df = threads.deferToThread(shadows.Netbox.cleanup_replaced_netbox,
                                   netbox_id, new_type)
        df.addCallback(reset)
        return df



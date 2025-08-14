#
# Copyright (C) 2008-2012 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Handle scheduling of polling jobs."""

import logging
import datetime
import time
from operator import itemgetter
from collections import defaultdict
from random import randint
from math import ceil

from django.db.transaction import atomic
from twisted.python.failure import Failure
from twisted.internet import task, reactor
from twisted.internet.defer import Deferred
from twisted.internet.task import LoopingCall
from twisted.python.log import err

from nav import ipdevpoll
from nav.ipdevpoll import db
from nav.ipdevpoll.snmp import SnmpError, AgentProxy
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import metric_prefix_for_ipdevpoll_job
from nav.tableformat import SimpleTableFormatter

from nav.ipdevpoll.utils import log_unhandled_failure

from . import shadows, config, signals
from .dataloader import NetboxLoader
from .db import run_in_thread
from .jobs import JobHandler, AbortedJobError, SuggestedReschedule
from ..models.event import EventQueue

_logger = logging.getLogger(__name__)


class NetboxJobScheduler(object):
    """Netbox job schedule handler.

    An instance of this class takes care of scheduling, running and
    rescheduling of a single JobHandler for a single netbox.

    """

    job_counters = {}
    job_queues = {}
    global_job_queue = []
    global_intensity = config.ipdevpoll_conf.getint('ipdevpoll', 'max_concurrent_jobs')
    _logger = ipdevpoll.ContextLogger()

    def __init__(self, job, netbox, pool):
        self.job = job
        self.netbox = netbox
        self.pool = pool
        self._log_context = dict(job=job.name, sysname=netbox.sysname)
        self._logger.debug(
            "initializing %r job scheduling for %s", job.name, netbox.sysname
        )
        self.cancelled = False
        self._deferred = Deferred()
        self._next_call = None
        self._last_job_started_at = 0
        self.running = False
        self._start_time = None
        self._current_job = None
        self.callLater = reactor.callLater

    def get_current_runtime(self):
        """Returns time elapsed since the start of the job as a timedelta."""
        return datetime.datetime.now() - self._start_time

    def start(self):
        """Start polling schedule."""
        self._next_call = self.callLater(0, self.run_job)
        return self._deferred

    def cancel(self):
        """Cancel scheduling of this job for this box.

        Future runs will not be scheduled after this.

        """
        if self.cancelled:
            self._logger.debug(
                "cancel: Job %r already cancelled for %s",
                self.job.name,
                self.netbox.sysname,
            )
            return

        if self._next_call.active():
            self._next_call.cancel()
            self._logger.debug(
                "cancel: Job %r cancelled for %s", self.job.name, self.netbox.sysname
            )
        else:
            self._logger.debug(
                "cancel: Job %r cancelled for %s, though no next run was scheduled",
                self.job.name,
                self.netbox.sysname,
            )

        self.cancelled = True
        self.cancel_running_job()
        self._deferred.callback(self)

    def cancel_running_job(self):
        if self._current_job:
            self._logger.debug('Cancelling running job')
            self.pool.cancel(self._current_job)

    def run_job(self, dummy=None):
        if self.is_running():
            self._logger.info(
                "Previous %r job is still running for %s, not running again now.",
                self.job.name,
                self.netbox.sysname,
            )
            return

        if self.is_job_limit_reached():
            self._logger.debug(
                "intensity limit reached for %s - waiting to run for %s",
                self.job.name,
                self.netbox.sysname,
            )
            self.queue_myself(self.get_job_queue())
            return

        if self.is_global_limit_reached():
            self._logger.debug(
                "global intensity limit reached - waiting to run for %s",
                self.netbox.sysname,
            )
            self.queue_myself(self.global_job_queue)
            return

        # We're ok to start a polling run.
        try:
            self._start_time = datetime.datetime.now()
            deferred = self.pool.execute_job(
                self.job.name,
                self.netbox.id,
                plugins=self.job.plugins,
                interval=self.job.interval,
            )
            self._current_job = deferred
        except Exception:  # noqa: BLE001
            self._log_unhandled_error(Failure())
            self.reschedule(60)
            return

        self.count_job()
        self._last_job_started_at = time.time()

        deferred.addErrback(self._adjust_intensity_on_snmperror)
        deferred.addCallbacks(self._reschedule_on_success, self._reschedule_on_failure)
        deferred.addErrback(self._log_unhandled_error)

        deferred.addCallback(self._unregister_handler)

    def is_running(self):
        return self.running

    @classmethod
    def _adjust_intensity_on_snmperror(cls, failure):
        if failure.check(AbortedJobError) and isinstance(
            failure.value.cause, SnmpError
        ):
            open_sessions = AgentProxy.count_open_sessions()
            new_limit = int(ceil(open_sessions * 0.90))
            if new_limit < cls.global_intensity:
                cls._logger.warning("Setting global intensity limit to %d", new_limit)
                cls.global_intensity = new_limit
        return failure

    def _update_counters(self, success):
        prefix = metric_prefix_for_ipdevpoll_job(self.netbox.sysname, self.job.name)
        counter_path = prefix + (".success-count" if success else ".failure-count")
        _COUNTERS.increment(counter_path)
        _COUNTERS.start()

    def _reschedule_on_success(self, result):
        """Reschedules the next normal run of this job."""
        delay = max(0, self.job.interval - self.get_runtime())
        self.reschedule(delay)
        if result:
            self._log_finished_job(True)
        else:
            self._logger.debug("job did nothing")
        self._update_counters(True if result else None)
        return result

    def _reschedule_on_failure(self, failure):
        """Examines the job failure and reschedules the job if needed."""
        if failure.check(SuggestedReschedule):
            delay = int(failure.value.delay)
        else:
            # within 5-10 minutes, but no longer than set interval
            delay = min(self.job.interval, randint(5 * 60, 10 * 60))
        self.reschedule(delay)
        self._log_finished_job(False)
        self._update_counters(False)
        failure.trap(AbortedJobError)

    def _log_finished_job(self, success=True):
        status = "completed" if success else "failed"
        runtime = datetime.timedelta(seconds=self.get_runtime())
        next_time = self.get_time_to_next_run()
        if next_time is not None:
            if next_time <= 0:
                delta = "right now"
            else:
                delta = "in %s" % datetime.timedelta(seconds=next_time)
            self._logger.info(
                "%s for %s %s in %s. next run %s.",
                self.job.name,
                self.netbox.sysname,
                status,
                runtime,
                delta,
            )
        else:
            self._logger.info("%s in %s. no next run scheduled", status, runtime)

    def get_runtime(self):
        """Returns the number of seconds passed since the start of last job"""
        return time.time() - self._last_job_started_at

    def get_time_to_next_run(self):
        """Returns the number of seconds until the next job starts"""
        if self._next_call.active():
            return self._next_call.getTime() - time.time()

    def reschedule(self, delay):
        """Reschedules the next run of of this job"""
        if self.cancelled:
            self._logger.debug("ignoring request to reschedule cancelled job")
            return

        next_time = datetime.datetime.now() + datetime.timedelta(seconds=delay)

        self._logger.debug(
            "Next %r job for %s will be in %d seconds (%s)",
            self.job.name,
            self.netbox.sysname,
            delay,
            next_time,
        )

        if self._next_call.active():
            self._next_call.reset(delay)
        else:
            self._next_call = self.callLater(delay, self.run_job)

    def _log_unhandled_error(self, failure):
        if not failure.check(db.ResetDBConnectionError):
            log_unhandled_failure(
                self._logger, failure, "Unhandled exception raised by JobHandler"
            )

    def _unregister_handler(self, result):
        """Remove a JobHandler from internal data structures."""
        if self.running:
            self.uncount_job()
            self.unqueue_next_job()
            self.unqueue_next_global_job()
        return result

    def count_job(self):
        current_count = self.__class__.job_counters.get(self.job.name, 0)
        current_count += 1
        self.__class__.job_counters[self.job.name] = current_count
        self.running = True

    def uncount_job(self):
        current_count = self.__class__.job_counters.get(self.job.name, 0)
        current_count -= 1
        self.__class__.job_counters[self.job.name] = max(current_count, 0)
        self.running = False
        self._current_job = None

    def get_job_count(self):
        return self.__class__.job_counters.get(self.job.name, 0)

    def is_job_limit_reached(self):
        "Returns True if the number of jobs >= the job intensity limit"
        return self.job.intensity > 0 and self.get_job_count() >= self.job.intensity

    @classmethod
    def is_global_limit_reached(cls):
        "Returns True if the global number of jobs >= global intensity limit"
        return cls.get_global_job_count() >= cls.global_intensity

    @classmethod
    def get_global_job_count(cls):
        if cls.job_counters:
            return sum(cls.job_counters.values())
        else:
            return 0

    def queue_myself(self, queue):
        queue.append(self)

    def unqueue_next_job(self):
        "Unqueues the next waiting job"
        queue = self.get_job_queue()
        if queue and not self.is_job_limit_reached():
            handler = queue.pop(0)
            return handler.start()

    @classmethod
    def unqueue_next_global_job(cls):
        "Unqueues the next job waiting because of the global intensity setting"
        if not cls.is_global_limit_reached():
            for index, handler in enumerate(cls.global_job_queue):
                if not handler.is_job_limit_reached():
                    del cls.global_job_queue[index]
                    return handler.start()

    def get_job_queue(self):
        if self.job.name not in self.job_queues:
            self.job_queues[self.job.name] = []
        return self.job_queues[self.job.name]


class JobScheduler(object):
    active_schedulers = set()
    job_logging_loop = None
    netbox_reload_interval = 2 * 60.0  # seconds
    netbox_reload_loop = None
    _logger = ipdevpoll.ContextLogger()

    def __init__(self, job, pool):
        """Initializes a job schedule from the job descriptor."""
        self._log_context = dict(job=job.name)
        self.job = job
        self.pool = pool
        self.netboxes = NetboxLoader()
        self.active_netboxes: dict[int, NetboxJobScheduler] = {}

        self.active_schedulers.add(self)

    def __repr__(self):
        return "<{} job={}>".format(self.__class__.__name__, self.job.name)

    @classmethod
    def get_job_schedulers_by_name(cls) -> dict[str, 'JobScheduler']:
        """Returns the names of actively scheduled jobs in this process"""
        return {scheduler.job.name: scheduler for scheduler in cls.active_schedulers}

    @classmethod
    def initialize_from_config_and_run(cls, pool, onlyjob=None):
        descriptors = config.get_jobs()
        schedulers = [
            JobScheduler(d, pool)
            for d in descriptors
            if not onlyjob or (d.name == onlyjob)
        ]
        for scheduler in schedulers:
            scheduler.run()

    def run(self):
        """Initiate scheduling of this job."""
        signals.netbox_type_changed.connect(self.on_netbox_type_changed)
        self._setup_active_job_logging()
        self._start_netbox_reload_loop()

    def _start_netbox_reload_loop(self):
        if not self.netbox_reload_loop:
            self.netbox_reload_loop = task.LoopingCall(self._reload_netboxes)
        if self.netbox_reload_loop.running:
            self.netbox_reload_loop.stop()

        def die_on_unhandled_failure(failure):
            err(failure, "Unhandled failure in data reload loop, stopping ipdevpoll")
            if reactor.running:
                reactor.callLater(0, reactor.stop)

        deferred = self.netbox_reload_loop.start(
            interval=self.netbox_reload_interval, now=True
        )
        deferred.addErrback(die_on_unhandled_failure)

    def on_netbox_type_changed(self, netbox_id, new_type, **_kwargs):
        """Performs various cleanup and reload actions on a netbox type change
        signal.

        The netbox' data are cleaned up, and the next netbox data reload is
        scheduled to take place immediately.

        """
        sysname = (
            netbox_id in self.netboxes
            and self.netboxes[netbox_id].sysname
            or str(netbox_id)
        )
        self._logger.info("Cancelling all jobs for %s due to type change.", sysname)
        self.cancel_netbox_scheduler(netbox_id)

        df = db.run_in_thread(
            shadows.Netbox.cleanup_replaced_netbox, netbox_id, new_type
        )
        return df.addCallback(lambda x: self._start_netbox_reload_loop())

    def _setup_active_job_logging(self):
        if self.__class__.job_logging_loop is None:
            loop = task.LoopingCall(self.__class__.log_active_jobs)
            self.__class__.job_logging_loop = loop
            loop.start(interval=5 * 60.0, now=False)

    def _reload_netboxes(self):
        """Reload the set of netboxes to poll and update schedules."""
        deferred = self.netboxes.load_all()
        deferred.addCallbacks(
            self._process_reloaded_netboxes, self._handle_reload_failures
        )
        db.django_debug_cleanup()
        return deferred

    def _process_reloaded_netboxes(self, result):
        """Process the result of a netbox reload and update schedules."""
        (new_ids, removed_ids, changed_ids) = result

        # Deschedule removed and changed boxes
        for netbox_id in removed_ids.union(changed_ids):
            self.cancel_netbox_scheduler(netbox_id)

        # Schedule new and changed boxes
        def _lastupdated(netboxid):
            return self.netboxes[netboxid].last_updated.get(
                self.job.name, datetime.datetime.min
            )

        new_and_changed = sorted(new_ids.union(changed_ids), key=_lastupdated)
        for netbox_id in new_and_changed:
            self.add_netbox_scheduler(netbox_id)

    def _handle_reload_failures(self, failure):
        failure.trap(db.ResetDBConnectionError)
        self._logger.error(
            "Reloading the IP device list failed because the "
            "database connection was reset"
        )

    def add_netbox_scheduler(self, netbox_id):
        netbox = self.netboxes[netbox_id]
        scheduler = NetboxJobScheduler(self.job, netbox, self.pool)
        self.active_netboxes[netbox_id] = scheduler
        return scheduler.start()

    def cancel_netbox_scheduler(self, netbox_id):
        if netbox_id not in self.active_netboxes:
            return
        scheduler = self.active_netboxes[netbox_id]
        scheduler.cancel()
        del self.active_netboxes[netbox_id]

    @classmethod
    def reload(cls):
        """Reload netboxes for all jobs"""
        for scheduler in cls.active_schedulers:
            scheduler._reload_netboxes()

    @classmethod
    def log_active_jobs(cls, level=logging.DEBUG):
        """Debug logs a list of running job handlers.

        The handlers will be sorted by descending runtime.

        """
        jobs = [
            (
                netbox_scheduler.netbox.sysname,
                netbox_scheduler.job.name,
                netbox_scheduler.get_current_runtime(),
            )
            for scheduler in cls.active_schedulers
            for netbox_scheduler in scheduler.active_netboxes.values()
            if netbox_scheduler.is_running()
        ]
        jobs.sort(key=itemgetter(2), reverse=True)
        table_formatter = SimpleTableFormatter(jobs)

        _logger = logging.getLogger("%s.joblist" % __name__)
        if jobs:
            _logger.log(
                level, "currently active jobs (%d):\n%s", len(jobs), table_formatter
            )
        else:
            _logger.log(
                level,
                "no active jobs (%d JobHandlers)",
                JobHandler.get_instance_count(),
            )


class CounterFlusher(defaultdict):
    """
    A dictionary of counters that can be incremented and be flushed as
    Graphite metrics at specific intervals.
    """

    def __init__(self, interval=60):
        """
        Initialize a dictionary of counters.

        :param interval: How often (in seconds) to flush the counters to
                         a Carbon backend.
        """
        super(CounterFlusher, self).__init__(int)
        self.loop = LoopingCall(self.flush)
        self.interval = interval

    def start(self):
        """Starts the counter flushing task if it isn't running already"""
        if not self.loop.running:
            self.loop.start(self.interval, now=False)

    def increment(self, name):
        """Increments a named counter by one"""
        self[name] += 1

    def flush(self):
        """
        Flushes all the counters to the Carbon backend and resets them to zero
        """
        if not self:
            _logger.debug("no counters to flush yet")

        _logger.debug("flushing %d counters to graphite", len(self))
        metrics = []
        timestamp = time.time()
        for counter, count in self.items():
            metrics.append((counter, (timestamp, count)))
            self[counter] = 0

        send_metrics(metrics)


_COUNTERS = CounterFlusher()


def handle_incoming_events():
    """Checks the event queue for events addressed to ipdevpoll and handles them"""
    # Since this extensively accesses the database, it needs to run in a thread:
    return run_in_thread(_handle_incoming_events)


@atomic
def _handle_incoming_events():
    events = EventQueue.objects.filter(target='ipdevpoll')
    # Filter out (and potentially delete) events not worthy of our attention
    events = [event for event in events if _event_pre_filter(event)]

    boxes_to_reschedule = defaultdict(list)
    # There may be multiple notifications queued for the same request, so group them
    # by netbox+jobname
    for event in events:
        boxes_to_reschedule[(event.netbox_id, event.subid)].append(event)
    _logger.debug("boxes_to_reschedule: %r", boxes_to_reschedule)

    _reschedule_jobs(boxes_to_reschedule)


def _reschedule_jobs(boxes_to_reschedule: dict[tuple[int, str], list[EventQueue]]):
    job_schedulers = JobScheduler.get_job_schedulers_by_name()
    for (netbox_id, job_name), events in boxes_to_reschedule.items():
        first_event = events[0]
        job_scheduler = job_schedulers[job_name]
        netbox_scheduler = job_scheduler.active_netboxes[netbox_id]
        _logger.info(
            "Re-scheduling immediate %s run for %s as requested by %s",
            first_event.netbox,
            job_name,
            first_event.source,
        )
        # Ensure all re-scheduling happens in the main reactor thread:
        reactor.callFromThread(netbox_scheduler.reschedule, 0)
        # now we can safely delete all the events
        for event in events:
            event.delete()


def _event_pre_filter(event: EventQueue):
    """Returns True if this event is worthy of this process' attention. If the event
    isn't worthy of *any* ipdevpoll process' attention, we delete it from the database
    too.
    """
    _logger.debug("Found event on queue: %r", event)
    if not _is_valid_refresh_event(event):
        event.delete()
        return False
    if not _is_refresh_event_for_me(event):
        return False
    return True


def _is_valid_refresh_event(event: EventQueue) -> bool:
    """Returns True if the event seems to be a valid refresh event for ipdevpoll."""
    if event.event_type_id != 'notification':
        _logger.info("Ignoring non-notification event from %s", event.source)
        return False

    if event.subid not in _get_valid_job_names():
        _logger.info(
            "Ignoring notification event from %s with unknown job name %r",
            event.source,
            event.subid,
        )
        return False

    return True


def _get_valid_job_names() -> set[str]:
    """Returns a set of job names that exist in the ipdevpoll configuration"""
    return set(job.name for job in config.get_jobs())


def _is_refresh_event_for_me(event: EventQueue):
    schedulers = JobScheduler.get_job_schedulers_by_name()
    if event.subid not in schedulers:
        _logger.debug(
            "This process does not schedule %s, %r is not for us", event.subid, event
        )
        return False

    if event.netbox_id not in schedulers[event.subid].netboxes:
        _logger.debug(
            "This process does not poll from %s, %r is not for us", event.netbox, event
        )
        return False

    return True

#
# Copyright (C) 2017, 2020 Uninett AS
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
"""Handle sending jobs to worker processes."""

import datetime
import os
import signal
import sys
import logging

from twisted.protocols import amp
from twisted.internet import reactor, protocol
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import ProcessEndpoint, StandardIOEndpoint
import twisted.internet.endpoints

from nav.ipdevpoll.config import ipdevpoll_conf
from . import control, jobs


def initialize_worker():
    """Initializes AMP server for a worker process"""
    handler = JobHandler()
    factory = protocol.Factory()
    factory.protocol = lambda: ProcessAMP(is_worker=True, locator=handler)
    StandardIOEndpoint(reactor).listen(factory)
    return handler


class Cancel(amp.Command):
    """Represent a cancel message for sending to workers"""

    arguments = [
        (b'serial', amp.Integer()),
    ]
    response = []


class Shutdown(amp.Command):
    """Represent a shutdown message for sending to workers"""

    arguments = []
    response = []


class Ping(amp.Command):
    """Represents a ping command for sending to workers"""

    arguments = []
    response = [(b'result', amp.Unicode())]


class Job(amp.Command):
    """Represent a job for sending to a worker"""

    arguments = [
        (b'netbox', amp.Integer()),
        (b'job', amp.Unicode()),
        (b'plugins', amp.ListOf(amp.Unicode())),
        (b'interval', amp.Integer()),  # Needs to be included in database record.
        # Not used for scheduling
        (b'serial', amp.Integer()),  # Serial number needed for cancelling
    ]
    response = [(b'result', amp.Boolean()), (b'reschedule', amp.Integer())]
    errors = {
        jobs.AbortedJobError: b'AbortedJob',
    }


class JobHandler(amp.CommandLocator):
    """Resolve actions for jobs received over AMP"""

    _logger = logging.getLogger(__name__ + '.jobhandler')

    def __init__(self):
        super(JobHandler, self).__init__()
        self.jobs = dict()
        self.done = False

    def job_done(self, result, serial):
        """De-registers a finished job"""
        if serial in self.jobs:
            del self.jobs[serial]
        if self.done and not self.jobs:
            reactor.callLater(3, reactor.stop)
        return result

    @Job.responder
    def execute_job(self, netbox, job, plugins, interval, serial):
        """Executes a single job, as instructed by the scheduler"""
        self._logger.debug(
            "Process %s received job %s for netbox %s with plugins %s",
            os.getpid(),
            job,
            netbox,
            ",".join(plugins),
        )
        job = jobs.JobHandler(job, netbox, plugins, interval)
        self.jobs[serial] = job
        deferred = job.run()
        deferred.addBoth(self.job_done, serial)
        deferred.addCallback(lambda x: {'result': x, 'reschedule': 0})

        def handle_reschedule(failure):
            failure.trap(jobs.SuggestedReschedule)
            return {'reschedule': failure.value.delay, "result": False}

        deferred.addErrback(handle_reschedule)
        return deferred

    @Cancel.responder
    def cancel(self, serial):
        """Cancels a running job"""
        if serial in self.jobs:
            self.jobs[serial].cancel()
        return {}

    @Shutdown.responder
    def shutdown(self):
        """Shuts down the worker process"""
        self.done = True
        return {}

    @Ping.responder
    def ping(self):
        """Returns the string "pong" as a response to a ping"""
        return {"result": "pong"}

    def log_jobs(self):
        """Logs information about active jobs"""
        self._logger.info("Got %s active jobs", len(self.jobs))
        for job in self.jobs.values():
            self._logger.info("%s %s %s", job.name, job.netbox, ", ".join(job.plugins))


class ProcessAMP(amp.AMP):
    """Modify AMP protocol to allow running over process pipes"""

    def __init__(self, is_worker, **kwargs):
        super(ProcessAMP, self).__init__(**kwargs)
        self.is_worker = is_worker
        self.lost_handler = None

    def makeConnection(self, transport):
        """Overrides the base implementation to fake the required getPeer() and
        getHost() methods on the incoming process transport object, if needed ( the
        base AMP class was not really designed with process pipe transports in mind,
        but with IP transports).

        Process transports in Twisted<21 did not implement these methods at all,
        while in Twisted>=21 they resolve to base methods that raise
        `NotImplementError`.
        """
        try:
            transport.getPeer()
        except (AttributeError, NotImplementedError):
            setattr(transport, 'getPeer', lambda: "peer")

        try:
            transport.getHost()
        except (AttributeError, NotImplementedError):
            setattr(transport, 'getHost', lambda: "host")

        super(ProcessAMP, self).makeConnection(transport)

    def connectionLost(self, reason):
        """Called when a connection to the AMP endpoint has been lost"""
        super(ProcessAMP, self).connectionLost(reason)
        if self.is_worker:
            if reactor.running:
                reactor.stop()
        else:
            if self.lost_handler:
                self.lost_handler(self, reason)


class InlinePool(object):
    """This is a dummy worker pool that executes all jobs in the current process"""

    def __init__(self):
        self.active_jobs = {}

    def job_done(self, result, deferred):
        """Cancels a running job"""
        if deferred in self.active_jobs:
            del self.active_jobs[deferred]
        return result

    def execute_job(self, job, netbox, plugins=None, interval=None):
        """Executes a single job, as instructed by the scheduler"""
        job = jobs.JobHandler(job, netbox, plugins, interval)
        deferred = job.run()
        self.active_jobs[deferred] = job
        deferred.addBoth(self.job_done, deferred)
        return deferred

    def cancel(self, deferred):
        """Cancels a running job"""
        if deferred in self.active_jobs:
            self.active_jobs[deferred].cancel()


class Worker(object):
    """This class holds information about one worker process as seen from
    the worker pool"""

    _logger = logging.getLogger(__name__ + '.worker')

    def __init__(self, pool, threadpoolsize, max_jobs):
        self._pid = None
        self.process = None
        self.active_jobs = 0
        self.total_jobs = 0
        self.max_concurrent_jobs = 0
        self.pool = pool
        self.threadpoolsize = threadpoolsize
        self.max_jobs = max_jobs
        self.started_at = None
        self._ping_loop = twisted.internet.task.LoopingCall(
            self._euthanize_unresponsive_worker,
            timeout=ipdevpoll_conf.getint("multiprocess", "ping_timeout", fallback=10),
        )

    def __repr__(self):
        return (
            "<Worker pid={pid} ready={ready} active={active} max={max} "
            "total={total} started_at={started_at}>"
        ).format(
            pid=self.pid,
            ready=not self.done(),
            active=self.active_jobs,
            max=self.max_concurrent_jobs,
            total=self.total_jobs,
            started_at=self.started_at,
        )

    @inlineCallbacks
    def start(self):
        """Starts a new child worker process"""
        args = [control.get_process_command(), '--worker', '-f', '-s', '-P']
        if self.threadpoolsize:
            args.append('--threadpoolsize=%d' % self.threadpoolsize)
        endpoint = ProcessEndpoint(
            reactor, control.get_process_command(), args, os.environ
        )
        factory = protocol.Factory()
        factory.protocol = lambda: ProcessAMP(is_worker=False, locator=JobHandler())
        self.process = yield endpoint.connect(factory)
        self.process.lost_handler = self._worker_died
        self.started_at = datetime.datetime.now()
        self._logger.debug("Started new worker %r", self)

        if ipdevpoll_conf.getboolean("multiprocess", "ping_workers", fallback=True):
            self._ping_loop.start(
                interval=ipdevpoll_conf.getint(
                    "multiprocess", "ping_interval", fallback=30
                ),
                now=False,
            )

        return self

    @property
    def pid(self):
        """Returns the PID number of the worker process, if started"""
        try:
            if not self._pid:
                self._pid = self.process.transport._process.pid
        except AttributeError:
            return None
        return self._pid

    def done(self):
        """Returns True if this worker process will take no more jobs"""
        return self.max_jobs and (self.total_jobs >= self.max_jobs)

    def _worker_died(self, _process, _reason):
        if self._ping_loop.running:
            self._ping_loop.stop()
        if not self.done():
            self._logger.warning("Lost worker: %r", self)
        elif self.active_jobs:
            self._logger.warning("Exited with active jobs: %r", self)
        else:
            self._logger.debug("Exited normally: %r", self)
        self.pool.worker_died(self)

    @inlineCallbacks
    def _euthanize_unresponsive_worker(self, timeout=10):
        """Sends the ping command to the worker. If the ping command does not succeed
        within the configured timeout, the worker is killed using the SIGTERM signal,
        under the assumption the process has frozen somehow.
        """
        is_alive = not self.done()  # assume the best
        if not self.done():
            try:
                is_alive = yield self.responds_to_ping(timeout)
            except twisted.internet.defer.TimeoutError:
                self._logger.warning("PING: Timed out for %r", self)
                is_alive = False
            except Exception:  # noqa: BLE001
                self._logger.exception(
                    "PING: Unhandled exception while pinging %r", self
                )
                is_alive = None

        # check again; no need to kill worker if its status became 'done'while waiting
        if not self.done():
            try:
                if not is_alive:
                    self._logger.warning(
                        "PING: Not responding, attempting to kill: %r", self
                    )
                    os.kill(self.pid, signal.SIGTERM)
            except Exception:  # noqa: BLE001
                self._logger.exception(
                    "PING: Ignoring unhandled exception when killing worker %r", self
                )

    def execute(self, serial, command, **kwargs):
        """Executes a remote job"""
        self.active_jobs += 1
        self.total_jobs += 1
        self.max_concurrent_jobs = max(self.active_jobs, self.max_concurrent_jobs)
        self._logger.debug(
            "Dispatching to process %s job %s for netbox %s with plugins %s "
            "(serial=%r)",
            self.pid,
            kwargs.get("job"),
            kwargs.get("netbox"),
            ",".join(kwargs.get("plugins", [])),
            serial,
        )
        deferred = self.process.callRemote(command, serial=serial, **kwargs)
        if self.done():
            self.process.callRemote(Shutdown)
        return deferred

    @inlineCallbacks
    def responds_to_ping(self, timeout=10):
        """Verifies that this worker is alive.

        :param timeout: The maximum allowable number of seconds for the worker to
                        respond
        :type timeout: int
        :return: A Deferred whose result will be True if the worker process responded
                 correctly and within the set timeout.
        """
        self._logger.debug("PING: %r", self)
        deferred = self.process.callRemote(Ping)
        response = yield deferred.addTimeout(timeout, clock=reactor)
        self._logger.debug("PING: Response from %r: %r", self, response)
        return response.get("result") == "pong"

    def cancel(self, serial):
        """Cancels a job running on this worker"""
        return self.process.callRemote(Cancel, serial=serial)


class WorkerPool(object):
    """This class represent a pool of worker processes to which jobs can
    be scheduled"""

    _logger = logging.getLogger(__name__ + '.workerpool')

    def __init__(self, workers, max_jobs, threadpoolsize=None):
        twisted.internet.endpoints.log = HackLog
        self.workers = set()
        self.target_count = workers
        self.max_jobs = max_jobs
        self.threadpoolsize = threadpoolsize
        for _ in range(self.target_count):
            self._spawn_worker()
        self.serial = 0
        self.jobs = dict()

    def worker_died(self, worker):
        """Called to signal the death of a worker process"""
        self.workers.remove(worker)
        if not worker.done():
            self._spawn_worker()

    @inlineCallbacks
    def _spawn_worker(self):
        worker = yield Worker(self, self.threadpoolsize, self.max_jobs).start()
        self.workers.add(worker)

    def _cleanup(self, result, deferred):
        _serial, worker = self.jobs[deferred]
        del self.jobs[deferred]
        worker.active_jobs -= 1
        return result

    def _execute(self, command, **kwargs):
        ready_workers = [w for w in self.workers if not w.done()]
        if not ready_workers:
            raise RuntimeError("No ready workers")
        worker = min(ready_workers, key=lambda x: x.active_jobs)  # type: Worker
        self.serial += 1
        deferred = worker.execute(self.serial, command, **kwargs)
        if worker.done():
            self._spawn_worker()
        self.jobs[deferred] = (self.serial, worker)
        deferred.addBoth(self._cleanup, deferred)
        return deferred

    def cancel(self, deferred):
        """Cancels a job running in the pool"""
        if deferred not in self.jobs:
            self._logger.debug("Cancelling job that isn't known")
            return
        serial, worker = self.jobs[deferred]
        return worker.cancel(serial)

    def execute_job(self, job, netbox, plugins=None, interval=None):
        """Executes a single job on an available worker"""
        deferred = self._execute(
            Job, job=job, netbox=netbox, plugins=plugins, interval=interval
        )

        def handle_reschedule(result):
            reschedule = result.get('reschedule', 0)
            if reschedule:
                raise jobs.SuggestedReschedule(delay=reschedule)
            return result

        deferred.addCallback(handle_reschedule)
        deferred.addCallback(lambda x: x['result'])
        return deferred

    def log_summary(self):
        """Logs a summary of currently running workers"""
        self._logger.info(
            "%s out of %s workers running", len(self.workers), self.target_count
        )
        for worker in self.workers:
            self._logger.info(" - %r", worker)


class HackLog(object):
    """Used to monkeypatch twisted.endpoints to log worker output the
    ipdevpoll way"""

    @staticmethod
    def msg(data, **_kwargs):
        """Logs a message to STDERR"""
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        sys.stderr.write(data)
        sys.stderr.flush()

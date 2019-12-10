#
# Copyright (C) 2017 Uninett AS
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
from __future__ import print_function
import os
import sys

from twisted.protocols import amp
from twisted.internet import reactor, protocol
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.endpoints import ProcessEndpoint, StandardIOEndpoint
import twisted.internet.endpoints

from django.utils import six

from nav.ipdevpoll import ContextLogger
from . import control, jobs


def initialize_worker():
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
    response = [(b'result', amp.Boolean()),
                (b'reschedule', amp.Integer())]
    errors = {
        jobs.AbortedJobError: b'AbortedJob',
    }


class JobHandler(amp.CommandLocator):
    """Resolve actions for jobs received over AMP"""

    _logger = ContextLogger()

    def __init__(self):
        super(JobHandler, self).__init__()
        self.jobs = dict()
        self.done = False

    def job_done(self, result, serial):
        if serial in self.jobs:
            del self.jobs[serial]
        if self.done and not self.jobs:
            reactor.callLater(3, reactor.stop)
        return result

    @Job.responder
    def execute_job(self, netbox, job, plugins, interval, serial):
        self._logger.debug("Process {pid} received job {job} for"
                           " netbox {netbox}"
                           " with plugins {plugins}".format(
                               pid=os.getpid(),
                               job=job,
                               netbox=netbox,
                               plugins=",".join(plugins)),)
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
        if serial in self.jobs:
            self.jobs[serial].cancel()
        return {}

    @Shutdown.responder
    def shutdown(self):
        self.done = True
        return {}

    def log_jobs(self):
        self._logger.info("Got {jobs} active jobs".format(
            jobs=len(self.jobs)))
        for job in self.jobs.values():
            self._logger.info("{job} {netbox} {plugins}".format(
                job=job.name,
                netbox=job.netbox,
                plugins=", ".join(job.plugins)))


class ProcessAMP(amp.AMP):
    """Modify AMP protocol to allow running over process pipes"""

    _logger = ContextLogger()

    def __init__(self, is_worker, **kwargs):
        super(ProcessAMP, self).__init__(**kwargs)
        self.is_worker = is_worker
        self.lost_handler = None

    def makeConnection(self, transport):
        if not hasattr(transport, 'getPeer'):
            setattr(transport, 'getPeer', lambda: "peer")
        if not hasattr(transport, 'getHost'):
            setattr(transport, 'getHost', lambda: "host")
        super(ProcessAMP, self).makeConnection(transport)

    def connectionLost(self, reason):
        super(ProcessAMP, self).connectionLost(reason)
        if self.is_worker:
            if reactor.running:
                reactor.stop()
        else:
            if self.lost_handler:
                self.lost_handler(self, reason)


class InlinePool(object):
    "This is a dummy worker pool that executes all jobs in the current process"
    def __init__(self):
        self.active_jobs = {}

    def job_done(self, result, deferred):
        if deferred in self.active_jobs:
            del self.active_jobs[deferred]
        return result

    def execute_job(self, job, netbox, plugins=None, interval=None):
        job = jobs.JobHandler(job, netbox, plugins, interval)
        deferred = job.run()
        self.active_jobs[deferred] = job
        deferred.addBoth(self.job_done, deferred)
        return deferred

    def cancel(self, deferred):
        if deferred in self.active_jobs:
            self.active_jobs[deferred].cancel()


class Worker(object):
    """This class holds information about one worker process as seen from
    the worker pool"""

    _logger = ContextLogger()

    def __init__(self, pool, threadpoolsize, max_jobs):
        self.active_jobs = 0
        self.total_jobs = 0
        self.max_concurrent_jobs = 0
        self.pool = pool
        self.threadpoolsize = threadpoolsize
        self.max_jobs = max_jobs

    @inlineCallbacks
    def start(self):
        args = [control.get_process_command(), '--worker', '-f', '-s', '-P']
        if self.threadpoolsize:
            args.append('--threadpoolsize=%d' % self.threadpoolsize)
        endpoint = ProcessEndpoint(reactor, control.get_process_command(),
                                   args, os.environ)
        factory = protocol.Factory()
        factory.protocol = lambda: ProcessAMP(is_worker=False,
                                              locator=JobHandler())
        self.process = yield endpoint.connect(factory)
        self.process.lost_handler = self._worker_died
        returnValue(self)

    def done(self):
        return self.max_jobs and (self.total_jobs >= self.max_jobs)

    def _worker_died(self, worker, reason):
        if not self.done():
            self._logger.warning("Lost worker {worker} with {jobs} "
                                 "active jobs".format(
                                     worker=worker,
                                     jobs=self.active_jobs))
        elif self.active_jobs:
            self._logger.warning("Worker {worker} exited with {jobs} "
                                 "active jobs".format(
                                     worker=worker,
                                     jobs=self.active_jobs))
        else:
            self._logger.debug("Worker {worker} exited normally"
                               .format(worker=worker))
        self.pool.worker_died(self)

    def execute(self, serial, command, **kwargs):
        self.active_jobs += 1
        self.total_jobs += 1
        self.max_concurrent_jobs = max(self.active_jobs,
                                       self.max_concurrent_jobs)
        deferred = self.process.callRemote(command, serial=serial, **kwargs)
        if self.done():
            self.process.callRemote(Shutdown)
        return deferred

    def cancel(self, serial):
        return self.process.callRemote(Cancel, serial=serial)


class WorkerPool(object):
    """This class represent a pool of worker processes to which jobs can
    be scheduled"""

    _logger = ContextLogger()

    def __init__(self, workers, max_jobs, threadpoolsize=None):
        twisted.internet.endpoints.log = HackLog
        self.workers = set()
        self.target_count = workers
        self.max_jobs = max_jobs
        self.threadpoolsize = threadpoolsize
        for i in range(self.target_count):
            self._spawn_worker()
        self.serial = 0
        self.jobs = dict()

    def worker_died(self, worker):
        self.workers.remove(worker)
        if not worker.done():
            self._spawn_worker()

    @inlineCallbacks
    def _spawn_worker(self):
        worker = yield Worker(self, self.threadpoolsize, self.max_jobs).start()
        self.workers.add(worker)

    def _cleanup(self, result, deferred):
        serial, worker = self.jobs[deferred]
        del self.jobs[deferred]
        worker.active_jobs -= 1
        return result

    def _execute(self, command, **kwargs):
        ready_workers = [w for w in self.workers if not w.done()]
        if not ready_workers:
            raise RuntimeError("No ready workers")
        worker = min(ready_workers, key=lambda x: x.active_jobs)
        self.serial += 1
        deferred = worker.execute(self.serial, command, **kwargs)
        if worker.done():
            self._spawn_worker()
        self.jobs[deferred] = (self.serial, worker)
        deferred.addBoth(self._cleanup, deferred)
        return deferred

    def cancel(self, deferred):
        if deferred not in self.jobs:
            self._logger.debug("Cancelling job that isn't known")
            return
        serial, worker = self.jobs[deferred]
        return worker.cancel(serial)

    def execute_job(self, job, netbox, plugins=None, interval=None):
        deferred = self._execute(Job, job=job, netbox=netbox,
                                 plugins=plugins, interval=interval)

        def handle_reschedule(result):
            reschedule = result.get('reschedule', 0)
            if reschedule:
                raise jobs.SuggestedReschedule(delay=reschedule)
            return result

        deferred.addCallback(handle_reschedule)
        deferred.addCallback(lambda x: x['result'])
        return deferred

    def log_summary(self):
        self._logger.info("{active} out of {target} workers running".format(
            active=len(self.workers),
            target=self.target_count))
        for worker in self.workers:
            self._logger.info(" - ready {ready} active {active}"
                              " max {max} total {total}".format(
                                  ready=not worker.done(),
                                  active=worker.active_jobs,
                                  max=worker.max_concurrent_jobs,
                                  total=worker.total_jobs))


class HackLog(object):
    @staticmethod
    def msg(data, **kwargs):
        """Used to monkeypatch twisted.endpoints to log worker output the
        ipdevpoll way"""
        if six.PY3 and isinstance(data, six.binary_type):
            data = data.decode("utf-8")
        sys.stderr.write(data)

#
# Copyright (C) 2017 UNINETT AS
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
"""Handle sending jobs to worker processes."""
from __future__ import print_function
from collections import defaultdict
import os
import sys

from twisted.protocols import amp
from twisted.internet import reactor, protocol
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import ProcessEndpoint, StandardIOEndpoint
import twisted.internet.endpoints

from nav.ipdevpoll import ContextLogger
from . import control, jobs


def initialize_worker():
    handler = TaskHandler()
    factory = protocol.Factory()
    factory.protocol = lambda: ProcessAMP(is_worker=True, locator=handler)
    StandardIOEndpoint(reactor).listen(factory)
    return handler


class Cancel(amp.Command):
    """Represent a cancel message for sending to workers"""
    arguments = [
        ('serial', amp.Integer()),
    ]
    response = []


class Task(amp.Command):
    """Represent a task for sending to a worker"""
    arguments = [
        ('netbox', amp.Integer()),
        ('job', amp.String()),
        ('plugins', amp.ListOf(amp.String())),
        ('interval', amp.Integer()),  # Needs to be included in database record.
                                      # Not used for scheduling
        ('serial', amp.Integer()),  # Serial number needed for cancelling
    ]
    response = [('result', amp.Boolean())]
    errors = {
        jobs.AbortedJobError: 'AbortedJob',
        jobs.SuggestedReschedule: 'SuggestedReschedule',
    }


class TaskHandler(amp.CommandLocator):
    """Resolve actions for tasks received over AMP"""

    _logger = ContextLogger()

    def __init__(self):
        super(TaskHandler, self).__init__()
        self.tasks = dict()

    def task_done(self, result, serial):
        if serial in self.tasks:
            del self.tasks[serial]
        return result

    @Task.responder
    def perform_task(self, netbox, job, plugins, interval, serial):
        self._logger.debug("Process {pid} received job {job} for"
                           " netbox {netbox}"
                           " with plugins {plugins}".format(
                               pid=os.getpid(),
                               job=job,
                               netbox=netbox,
                               plugins=",".join(plugins)),)
        job = jobs.JobHandler(job, netbox, plugins, interval)
        self.tasks[serial] = job
        deferred = job.run()
        deferred.addBoth(self.task_done, serial)
        deferred.addCallback(lambda x: {'result': x})
        return deferred

    @Cancel.responder
    def cancel(self, serial):
        if serial in self.tasks:
            self.tasks[serial].cancel()
        return {}

    def log_tasks(self):
        self._logger.info("Got {tasks} active tasks".format(
            tasks=len(self.tasks)))
        for job in self.tasks.values():
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
    "This is a dummy worker pool that performs all tasks in the current process"
    def __init__(self):
        self.active_tasks = {}

    def job_done(self, result, deferred):
        if deferred in self.active_tasks:
            del self.active_tasks[deferred]
        return result

    def perform_task(self, job, netbox, plugins=None, interval=None):
        job = jobs.JobHandler(job, netbox, plugins, interval)
        deferred = job.run()
        self.active_tasks[deferred] = job
        deferred.addBoth(self.job_done, deferred)
        return deferred

    def cancel(self, deferred):
        if deferred in self.active_tasks:
            self.active_tasks[deferred].cancel()


class WorkerPool(object):
    """This class represent a pool of worker processes to which tasks can
    be scheduled"""

    _logger = ContextLogger()

    def __init__(self, workers, threadpoolsize=None):
        twisted.internet.endpoints.log = HackLog
        self.active_tasks = dict()
        self.max_tasks = defaultdict(int)
        self.total_tasks = defaultdict(int)
        self.target_count = workers
        self.threadpoolsize = threadpoolsize
        for i in range(self.target_count):
            self._spawn_worker()
        self.serial = 0
        self.tasks = dict()

    def _worker_died(self, worker, reason):
        self._logger.warning("Lost worker {worker} with {tasks} "
                             "active tasks".format(
                                 worker=worker,
                                 tasks=self.active_tasks.get(worker, 0)))
        del self.active_tasks[worker]
        self._spawn_worker()

    @inlineCallbacks
    def _spawn_worker(self):
        args = [control.get_process_command(), '--worker', '-f', '-s', '-P']
        if self.threadpoolsize:
            args.append('--threadpoolsize=%d' % self.threadpoolsize)
        endpoint = ProcessEndpoint(reactor, control.get_process_command(),
                                   args, os.environ)
        factory = protocol.Factory()
        factory.protocol = lambda: ProcessAMP(is_worker=False,
                                              locator=TaskHandler())
        worker = yield endpoint.connect(factory)
        worker.lost_handler = self._worker_died
        self.active_tasks[worker] = 0

    def _cleanup(self, result, deferred):
        serial, worker = self.tasks[deferred]
        del self.tasks[deferred]
        self.active_tasks[worker] -= 1
        return result

    def _execute(self, task, **kwargs):
        worker = min(self.active_tasks, key=lambda x: self.active_tasks[x])
        self.serial += 1
        self.active_tasks[worker] += 1
        self.total_tasks[worker] += 1
        self.max_tasks[worker] = max(self.active_tasks[worker],
                                     self.max_tasks[worker])
        deferred = worker.callRemote(task, serial=self.serial, **kwargs)
        self.tasks[deferred] = (self.serial, worker)
        deferred.addBoth(self._cleanup, deferred)
        return deferred

    def cancel(self, deferred):
        if deferred not in self.tasks:
            self._logger.debug("Cancelling job that isn't known")
            return
        serial, worker = self.tasks[deferred]
        return worker.callRemote(Cancel, serial=serial)

    def perform_task(self, job, netbox, plugins=None, interval=None):
        deferred = self._execute(Task, job=job, netbox=netbox,
                                 plugins=plugins, interval=interval)
        deferred.addCallback(lambda x: x['result'])
        return deferred

    def log_summary(self):
        self._logger.info("{active} out of {target} workers running".format(
            active=len(self.active_tasks),
            target=self.target_count))
        for i, worker in enumerate(self.active_tasks):
            self._logger.info(" - {i}: active {active}"
                              " max {max} total {total}".format(
                                  i=i, active=self.active_tasks[worker],
                                  max=self.max_tasks[worker],
                                  total=self.total_tasks[worker]))


class HackLog(object):
    @staticmethod
    def msg(data, **kwargs):
        """Used to monkeypatch twisted.endpoints to log worker output the
        ipdevpoll way"""
        sys.stderr.write(data)

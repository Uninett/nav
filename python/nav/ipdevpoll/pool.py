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
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.endpoints import ProcessEndpoint, StandardIOEndpoint
import twisted.internet.endpoints

from nav.ipdevpoll import ContextLogger
from . import control, jobs


def initialize_worker():
    factory = protocol.Factory()
    factory.protocol = lambda: ProcessAMP(locator=TaskHandler())
    StandardIOEndpoint(reactor).listen(factory)


class Task(amp.Command):
    """Represent a task for sending to a worker"""
    arguments = [
        ('netbox', amp.Integer()),
        ('job', amp.String()),
        ('plugins', amp.ListOf(amp.String())),
        ('interval', amp.Integer()),  # Needs to be included in database record.
                                      # Not used for scheduling
    ]
    response = [('result', amp.Boolean())]
    errors = {
        jobs.AbortedJobError: 'AbortedJob',
        jobs.SuggestedReschedule: 'SuggestedReschedule',
    }


class TaskHandler(amp.CommandLocator):
    """Resolve actions for tasks received over AMP"""

    _logger = ContextLogger()

    @Task.responder
    def perform_task(self, netbox, job, plugins, interval):
        self._logger.debug("Process {pid} received job {job} for"
                           " netbox {netbox}"
                           " with plugins {plugins}".format(
                               pid=os.getpid(),
                               job=job,
                               netbox=netbox,
                               plugins=",".join(plugins)),)
        job = jobs.JobHandler(job, netbox, plugins, interval)
        deferred = job.run()
        deferred.addCallback(lambda x: {'result': x})
        return deferred


class ProcessAMP(amp.AMP):
    """Modify AMP protocol to allow running over process pipes"""

    def makeConnection(self, transport):
        if not hasattr(transport, 'getPeer'):
            setattr(transport, 'getPeer', lambda: "peer")
        if not hasattr(transport, 'getHost'):
            setattr(transport, 'getHost', lambda: "host")
        super(ProcessAMP, self).makeConnection(transport)


class InlinePool(object):
    "This is a dummy worker pool that performs all tasks in the current process"
    def __init__(self):
        pass

    def perform_task(self, job, netbox, plugins=None, interval=None):
        job = jobs.JobHandler(job, netbox, plugins, interval)
        return job.run()


class WorkerPool(object):
    """This class represent a pool of worker processes to which tasks can
    be scheduled"""

    _logger = ContextLogger()

    def __init__(self, workers):
        twisted.internet.endpoints.log = HackLog
        self.activeTasks = dict()
        self.maxTasks = defaultdict(int)
        self.totalTasks = defaultdict(int)
        self.target_count = workers
        for i in range(self.target_count):
            self._spawn_worker()

    @inlineCallbacks
    def _spawn_worker(self, threadpoolsize=None):
        args = [control.get_process_command(), '--worker', '-f', '-s', '-P']
        if threadpoolsize:
            args.append('--threadpoolsize=%d' % threadpoolsize)
        endpoint = ProcessEndpoint(reactor, control.get_process_command(),
                                   args, os.environ)
        factory = protocol.Factory()
        factory.protocol = lambda: ProcessAMP(locator=TaskHandler())
        worker = yield endpoint.connect(factory)
        self.activeTasks[worker] = 0

    @inlineCallbacks
    def _execute(self, task, **kwargs):
        worker = min(self.activeTasks, key=lambda x: self.activeTasks[x])
        self.activeTasks[worker] += 1
        self.totalTasks[worker] += 1
        self.maxTasks[worker] = max(self.activeTasks[worker],
                                    self.maxTasks[worker])
        try:
            result = yield worker.callRemote(task, **kwargs)
        except:
            self._logger.exception("Unhandled exception")
            return
        finally:
            self.activeTasks[worker] -= 1
        returnValue(result)

    def perform_task(self, job, netbox, plugins=None, interval=None):
        return self._execute(Task, job=job, netbox=netbox,
                             plugins=plugins, interval=interval)

    def log_summary(self):
        self._logger.info("{active} out of {target} workers running".format(
            active=len(self.activeTasks),
            target=self.target_count))
        for i, worker in enumerate(self.activeTasks):
            self._logger.info(" - {i}: active {active}"
                              " max {max} total {total}".format(
                                  i=i, active=self.activeTasks[worker],
                                  max=self.maxTasks[worker],
                                  total=self.totalTasks[worker]))


class HackLog(object):
    @staticmethod
    def msg(data, **kwargs):
        """Used to monkeypatch twisted.endpoints to log worker output the
        ipdevpoll way"""
        sys.stderr.write(data)

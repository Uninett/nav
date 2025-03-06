# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
This module provides a threadpool and fair scheduling.
"""

from collections import deque
import heapq
import sys
import time
import threading
import logging


from . import config


_logger = logging.getLogger(__name__)


class TerminateException(Exception):
    """Raised to terminate the execution of a Worker"""


class Worker(threading.Thread):
    """
    The thread removes a checker from the runqueue and executes it. If the
    runque is empty, the thread sleeps until it gets woken when a checker is
    placed in the queue.

    """

    def __init__(self, rq):
        threading.Thread.__init__(self)
        self._runqueue = rq
        self._runcount = 0
        self._running = 1
        self._time_created = time.time()
        self._time_start_execute = 0

    def run(self):
        """
        Tries to dequeue a checker. Loops while
        self._running=1
        """
        while self._running:
            try:
                checker = self._runqueue.deq()
                self.execute(checker)
            except TerminateException:
                self._runqueue.workers.remove(self)
                return

    def execute(self, checker):
        """
        Executes the checker. If maximum runcount is
        exceeded, self._running is set to zero and the
        thread will be recycled.
        """
        self._runcount += 1
        self._time_start_execute = time.time()
        checker.run()
        if (
            self._runqueue.get_max_run_count() != 0
            and self._runcount > self._runqueue.get_max_run_count()
        ):
            self._running = 0
            self._runqueue.unused_thread_name.append(self.getName())
            self._runqueue.workers.remove(self)
            _logger.info("%s is recycling.", self.getName())
        _logger.debug("%s finished checker number %i", self.getName(), self._runcount)
        self._time_start_execute = 0


def RunQueue(*args, **kwargs):
    """Instantiates or retrieves the RunQueue singleton"""
    if getattr(_RunQueue, '_instance') is None:
        setattr(_RunQueue, '_instance', _RunQueue(*args, **kwargs))
    return getattr(_RunQueue, '_instance')


class _RunQueue(object):
    _instance = None

    def __init__(self, **kwargs):
        self.conf = config.serviceconf()
        self._max_threads = int(self.conf.get('maxthreads', sys.maxsize))
        _logger.info("Setting maxthreads=%i", self._max_threads)
        self._max_run_count = int(self.conf.get('recycle interval', 50))
        _logger.info("Setting maxRunCount=%i", self._max_run_count)
        self._controller = kwargs.get('controller', self)
        self.workers = []
        self.unused_thread_name = []
        self.queue = deque()
        self.timerqueue = EventQueue()
        self.lock = threading.RLock()
        self.await_work = threading.Condition(self.lock)
        self.stop = 0
        self.make_daemon = 1

    def get_max_run_count(self):
        return self._max_run_count

    def enq(self, runnable):
        """
        Enqueues a runnable in the runqueue. It accepts
        a runnable, or a tuple containing (timestamp, runnable).
        If given in the last form, the runnable will be run as
        quickly as possible after time timestamp has occured.
        """
        self.lock.acquire()
        # Checkers with priority is put in a seperate queue
        if isinstance(runnable, tuple):
            pri, obj = runnable
            self.timerqueue.put(pri, obj)
        else:
            self.queue.append(runnable)

        self._start_worker_if_needed()
        self.lock.release()

    def _start_worker_if_needed(self):
        # This is quite dirty, but I really need to know how many
        # threads are waiting for checkers.
        waiters = getattr(self.await_work, "_waiters", None)
        num_waiters = len(waiters)
        _logger.debug(
            "Number of workers: %i Waiting workers: %i", len(self.workers), num_waiters
        )
        if num_waiters > 0:
            self.await_work.notify()
        elif len(self.workers) < self._max_threads:
            new_worker = Worker(self)
            new_worker.setDaemon(self.make_daemon)
            if self.unused_thread_name:
                new_worker.setName(self.unused_thread_name.pop())
            else:
                new_worker.setName('worker' + str(len(self.workers)))
            self.workers.append(new_worker)
            new_worker.start()

    def deq(self):
        """
        Gets a runnable from the runqueue. Checks if we have
        scheduled checkers (runnables containing timestamp. If not, we
        return a checker without timestamp.
        """
        self.lock.acquire()
        while 1:
            # wait if we have no checkers in queue
            while not self.queue and not self.timerqueue:
                if self.stop:
                    self.lock.release()
                    raise TerminateException
                self.await_work.wait()
            if self.stop:
                self.lock.release()
                raise TerminateException

            if self.timerqueue:
                scheduled_time = float(self.timerqueue.firstTimestamp())
                now = time.time()
                wait = scheduled_time - now
                # If we have priority ready we
                # return it now.
                if wait <= 0:
                    r = self.timerqueue.pop()
                    self.lock.release()
                    return r
            # We have no priority checkers ready.
            # Check if we have unpriority checkers
            # to execute
            if self.queue:
                r = self.queue.popleft()
                self.lock.release()
                return r
            # Wait to execute priority checker, break if new checkers arrive
            else:
                _logger.debug("Thread waits for %s secs", wait)
                self.await_work.wait(wait)

    def terminate(self):
        """Terminates all worker threads"""
        self.lock.acquire()
        self.stop = 1
        self.await_work.notifyAll()
        self.lock.release()
        _logger.info("Waiting for threads to terminate...")
        for i in self.workers:
            i.join()
        _logger.info("All threads have finished")


class EventQueue(object):
    def __init__(self):
        self.heap = []
        self.counter = 0

    def put(self, timestamp, item):
        '''Insert item *item* in heap with the timestamp *timestamp*'''
        self.counter += 1
        heapq.heappush(self.heap, (timestamp, self.counter, item))

    def firstTimestamp(self):
        '''Returns the timestamp of the first event in the queue'''
        if not self.heap:
            raise IndexError("empty event queue")
        return self.heap[0][0]

    def pop(self):
        '''Removes and returns the first event in the queue'''
        timestamp, counter, item = heapq.heappop(self.heap)
        return item

    def __bool__(self):
        return bool(self.heap)

    def __len__(self):
        return len(self.heap)

# -*- coding: ISO8859-1 -*-
#
# Copyright 2003 Norwegian University of Science and Technology
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
#
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#
"""
This module provides a threadpool and fair scheduling.
"""
from threading import *
import threading
import DEQueue
import sys
import time
import types
import config
from debug import debug
import prioqueunique

class TerminateException(Exception):
    pass

class worker(threading.Thread):
    """
    The thread removes a checker from the runqueue and executes it. If the
    runque is empty, the thread sleeps until it gets woken when a checker is
    placed in the queue.

    """
    def __init__(self, rq):
        threading.Thread.__init__(self)
        self._runqueue=rq
        self._runcount=0
        self._running=1
        self._timeCreated=time.time()
        self._timeStartExecute=0

    def run(self):
        """
        Tries to dequeue a checker. Loops while
        self._running=1
        """
        while self._running:
            try:
                self._checker=self._runqueue.deq()
                self.execute()
            except TerminateException:
                self._runqueue.workers.remove(self)
                return

    def execute(self):
        """
        Executes the checker. If maximum runcount is
        exceeded, self._running is set to zero and the
        thread will be recycled.
        """
        self._runcount+=1
        self._timeStartExecute=time.time()
        self._checker.run()
        if self._runqueue.getMaxRunCount() != 0 and \
               self._runcount > self._runqueue.getMaxRunCount():
            self._running=0
            self._runqueue.unusedThreadName.append(self.getName())
            self._runqueue.workers.remove(self)
            debug("%s is recycling."% self.getName())
        debug("%s finished checker number %i" % (self.getName(), self._runcount),7)
        self._timeStartExecute=0


def RunQueue(*args, **kwargs):
    if _RunQueue._instance is None:
        _RunQueue._instance=_RunQueue(*args,**kwargs)
    return _RunQueue._instance

class _RunQueue:
    _instance=None
    def __init__(self,**kwargs):
        self.conf=config.serviceconf()
        self._maxThreads=int(self.conf.get('maxthreads', sys.maxint))
        debug("Setting maxthreads=%i" % self._maxThreads)
        self._maxRunCount=int(self.conf.get('recycle interval',50))
        debug("Setting maxRunCount=%i" % self._maxRunCount)
        self._controller=kwargs.get('controller',self)
        self.workers=[]
        self.unusedThreadName=[]
        self.rq=DEQueue.DEQueue()
        self.pq=prioqueunique.prioque()
        self.lock=RLock()
        self.awaitWork=Condition(self.lock)
        self.stop=0
        self.makeDaemon=1

    def getMaxRunCount(self):
        return self._maxRunCount

    def enq(self, runnable):
        """
        Enqueues a runnable in the runqueue. It accepts
        a runnable, or a tuple containing (timestamp, runnable).
        If given in the last form, the runnable will be run as
        quickly as possible after time timestamp has occured.
        """
        self.lock.acquire()
        # Checkers with priority is put in a seperate queue
        if type(runnable) == types.TupleType:
            pri,obj=runnable
            self.pq.put(pri,obj)
        else:
            self.rq.put(runnable)

        # This is quite dirty, but I really need to know how many
        # threads are waiting for checkers.
        numWaiters=len(self.awaitWork._Condition__waiters)
        debug("Number of workers: %i Waiting workers: %i" % \
              (len(self.workers), numWaiters), 7)
        if numWaiters > 0:
            self.awaitWork.notify()
        elif len(self.workers) < self._maxThreads:
            newWorker=worker(self)
            newWorker.setDaemon(self.makeDaemon)
            if len(self.unusedThreadName) > 0:
                newWorker.setName(self.unusedThreadName.pop())
            else:
                newWorker.setName('worker'+str(len(self.workers)))
            self.workers.append(newWorker)
            newWorker.start()
        self.lock.release()

    def deq(self):
        """
        Gets a runnable from the runqueue. Checks if we have
        scheduled checkers (runnables containing timestamp. If not, we
        return a checker without timestamp.
        self.pq = priorityqueue
        self.rq = queue
        """
        self.lock.acquire()
        while 1:
            # wait if we have no checkers in queue
            while len(self.rq)==0 and len(self.pq)==0:
                if self.stop:
                    self.lock.release()
                    raise TerminateException
                self.awaitWork.wait()
            if self.stop: 
                self.lock.release()
                raise TerminateException

            if len(self.pq)>0:
                scheduledTime, obj = self.pq.headPair()
                scheduledTime=float(scheduledTime)
                now=time.time()
                wait=scheduledTime-now
                # If we have priority ready we
                # return it now.
                if wait <= 0:
                    r=self.pq.get()
                    self.lock.release()
                    return r
            # We have no priority checkers ready.
            # Check if we have unpriority checkers
            # to execute
            if len(self.rq) > 0:
                r=self.rq.get()
                self.lock.release()
                return r
            # Wait to execute priority checker, break if new checkers arrive
            else:
                debug("Thread waits for %s secs" % wait,7)
                self.awaitWork.wait(wait)

    def terminate(self):
        self.lock.acquire()
        self.stop=1
        self.awaitWork.notifyAll()
        self.numThreadsWaiting=0
        self.lock.release()
        debug("Waiting for threads to terminate...")
        for i in self.workers:
            i.join()
        debug("All threads have finished")
